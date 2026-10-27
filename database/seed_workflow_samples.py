"""Add idempotent, TEST-labeled workflow samples to the configured SQLite DB."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.engine import make_url

from app import create_app
from app.models import (
    Asset,
    Department,
    Disposal,
    Inventory,
    InventoryDetail,
    Repair,
    Transfer,
    db,
)

MARKER = "[TEST-SAMPLE]"
INVENTORY_NAME = f"{MARKER} Kiểm kê mẫu - 10 kết quả đã ghi"
DEPARTMENT_CODES = ("TEST-TH", "TEST-VP", "TEST-KH", "TEST-TV")
REPAIR_STATUS_BY_INDEX = (
    "completed",
    "completed",
    "completed",
    "completed",
    "completed",
    "pending",
    "pending",
    "pending",
    "in_progress",
    "in_progress",
)


def seed_workflow_samples() -> dict[str, int]:
    """Seed ten records per workflow without duplicating existing sample rows."""
    app = create_app()
    if make_url(app.config["SQLALCHEMY_DATABASE_URI"]).get_backend_name() != "sqlite":
        raise RuntimeError("Workflow sample seeding is restricted to SQLite.")

    inserted = {
        "inventory_details_checked": 0,
        "disposals": 0,
        "transfers": 0,
        "repairs": 0,
    }
    with app.app_context():
        assets = (
            Asset.query.filter(Asset.asset_code.like("TEST-ASSET-%"))
            .order_by(Asset.asset_code)
            .all()
        )
        if len(assets) < 20:
            raise RuntimeError(
                "Expected at least 20 TEST-ASSET-* records; create the test asset "
                "dataset before seeding workflow samples."
            )
        test_assets = assets[:20]
        departments = {
            department.code: department
            for department in Department.query.filter(
                Department.code.in_(DEPARTMENT_CODES)
            ).all()
        }
        if set(departments) != set(DEPARTMENT_CODES):
            raise RuntimeError(
                "The four TEST departments are required before seeding workflow samples."
            )

        try:
            transfer_assets = test_assets[:10]
            repair_assets = test_assets[10:20]

            for index, asset in enumerate(transfer_assets):
                reason = (
                    f"{MARKER} transfer {asset.asset_code} - "
                    "điều chuyển mẫu phục vụ kiểm thử"
                )
                if Transfer.query.filter_by(reason=reason).first():
                    continue
                if asset.status != "active":
                    raise RuntimeError(
                        f"{asset.asset_code} must be active for the sample transfer."
                    )
                source = asset.department
                if source is None or source.code not in DEPARTMENT_CODES:
                    raise RuntimeError(
                        f"{asset.asset_code} is not assigned to a TEST department."
                    )
                destination_code = DEPARTMENT_CODES[
                    (DEPARTMENT_CODES.index(source.code) + 1) % len(DEPARTMENT_CODES)
                ]
                destination = departments[destination_code]
                db.session.add(
                    Transfer(
                        asset=asset,
                        from_department=source,
                        to_department=destination,
                        transfer_date=date.today() - timedelta(days=10 - index),
                        reason=reason,
                        notes=f"{MARKER} Dữ liệu minh họa, không phải lịch sử thật.",
                        performed_by="Người thực hiện TEST",
                    )
                )
                asset.department = destination
                inserted["transfers"] += 1

            for index, asset in enumerate(repair_assets):
                description = (
                    f"{MARKER} repair {asset.asset_code} - "
                    "yêu cầu sửa chữa mẫu phục vụ kiểm thử"
                )
                if Repair.query.filter_by(description=description).first():
                    continue
                status = REPAIR_STATUS_BY_INDEX[index]
                if status in {"pending", "in_progress"} and asset.status != "active":
                    raise RuntimeError(
                        f"{asset.asset_code} must be active for an open sample repair."
                    )
                request_date = date.today() - timedelta(days=20 - index)
                repair_date = (
                    request_date + timedelta(days=2)
                    if status == "completed"
                    else None
                )
                db.session.add(
                    Repair(
                        asset=asset,
                        request_date=request_date,
                        repair_date=repair_date,
                        status=status,
                        description=description,
                        cost=250_000 + index * 50_000,
                        notes=f"{MARKER} Dữ liệu minh họa, không phải lịch sử thật.",
                        requested_by="Người gửi yêu cầu TEST",
                        updated_by="Quản lý TEST",
                    )
                )
                if status in {"pending", "in_progress"}:
                    asset.status = "repair"
                inserted["repairs"] += 1

            disposal_statuses = ("requested",) * 5 + ("rejected",) * 5
            for index, (asset, status) in enumerate(
                zip(transfer_assets, disposal_statuses, strict=True)
            ):
                reason = (
                    f"{MARKER} disposal {asset.asset_code} - "
                    "đề nghị thanh lý mẫu phục vụ kiểm thử"
                )
                if Disposal.query.filter_by(reason=reason).first():
                    continue
                if asset.status != "active":
                    raise RuntimeError(
                        f"{asset.asset_code} must remain active for the sample disposal."
                    )
                requested_at = datetime.now().replace(microsecond=0)
                db.session.add(
                    Disposal(
                        asset=asset,
                        disposal_date=date.today() + timedelta(days=30),
                        reason=reason,
                        liquidation_value=100_000 + index * 25_000,
                        status=status,
                        requested_by="Người đề xuất TEST",
                        decided_by="Quản trị viên TEST" if status == "rejected" else None,
                        decided_at=requested_at if status == "rejected" else None,
                    )
                )
                inserted["disposals"] += 1

            campaign = Inventory.query.filter_by(name=INVENTORY_NAME).first()
            if campaign is None:
                campaign = Inventory(
                    name=INVENTORY_NAME,
                    start_date=date.today(),
                    status="pending",
                    created_by="Người tạo đợt TEST",
                )
                db.session.add(campaign)
                db.session.flush()

                campaign_assets = Asset.query.filter(
                    Asset.status != "disposal"
                ).order_by(Asset.asset_code).all()
                campaign.details = [
                    InventoryDetail(
                        asset=asset,
                        expected_status=asset.status,
                    )
                    for asset in campaign_assets
                ]

            checked_assets = [
                asset
                for asset in test_assets
                if asset.status != "disposal"
            ][:10]
            for index, asset in enumerate(checked_assets):
                detail = InventoryDetail.query.filter_by(
                    inventory_id=campaign.id,
                    asset_id=asset.id,
                ).first()
                if detail is None:
                    raise RuntimeError(
                        f"Inventory snapshot is missing {asset.asset_code}."
                    )
                if detail.actual_status is not None:
                    continue
                actual_status = "damaged" if index == 5 else detail.expected_status
                detail.actual_status = actual_status
                detail.variance_note = (
                    f"{MARKER} Tình trạng mẫu có sai lệch để kiểm thử đối chiếu."
                    if actual_status != detail.expected_status
                    else f"{MARKER} Đã kiểm đếm mẫu."
                )
                detail.checked_by = "Người kiểm kê TEST"
                detail.checked_at = datetime.now().replace(microsecond=0)
                inserted["inventory_details_checked"] += 1

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        checked_count = InventoryDetail.query.filter(
            InventoryDetail.inventory_id == campaign.id,
            InventoryDetail.actual_status.isnot(None),
            InventoryDetail.variance_note.like(f"{MARKER}%"),
        ).count()
        if checked_count < 10:
            raise RuntimeError(
                f"Expected at least 10 TEST inventory results; found {checked_count}."
            )

        totals = {
            "inventory_details_checked": checked_count,
            "disposals": Disposal.query.filter(
                Disposal.reason.like(f"{MARKER} disposal %")
            ).count(),
            "transfers": Transfer.query.filter(
                Transfer.reason.like(f"{MARKER} transfer %")
            ).count(),
            "repairs": Repair.query.filter(
                Repair.description.like(f"{MARKER} repair %")
            ).count(),
        }
        expected = {
            "inventory_details_checked": 10,
            "disposals": 10,
            "transfers": 10,
            "repairs": 10,
        }
        if totals != expected:
            raise RuntimeError(f"Unexpected sample record totals: {totals}")
        return inserted


def main() -> None:
    inserted = seed_workflow_samples()
    print("Workflow sample seeding complete (existing TEST data was preserved).")
    for workflow, count in inserted.items():
        print(f"{workflow}_inserted={count}")


if __name__ == "__main__":
    main()
