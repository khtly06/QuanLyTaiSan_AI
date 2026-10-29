"""Extend the configured SQLite database to 120 assets with balanced workflows."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.engine import make_url

from app import create_app
from app.models import (
    Asset,
    Category,
    Department,
    Disposal,
    Inventory,
    InventoryDetail,
    Repair,
    Transfer,
    db,
)

TARGET_ASSET_COUNT = 120
ASSET_NAMES = (
    "Máy tính để bàn Dell OptiPlex 7010",
    "Máy tính để bàn HP ProDesk 400 G9",
    "Máy tính để bàn Lenovo ThinkCentre M70s",
    "Máy tính xách tay Dell Latitude 5440",
    "Máy tính xách tay HP ProBook 440 G10",
    "Máy tính xách tay Lenovo ThinkPad E14",
    "Màn hình Dell P2422H 24 inch",
    "Màn hình HP E24 G5 24 inch",
    "Máy in laser Canon imageCLASS LBP246dw",
    "Máy in laser HP LaserJet Pro M404dn",
    "Máy quét tài liệu Epson WorkForce DS-410",
    "Máy photocopy Ricoh IM 2702",
    "Bộ phát Wi-Fi TP-Link Omada EAP610",
    "Bộ chuyển mạch mạng Cisco CBS250-24T",
    "Máy chủ lưu trữ dữ liệu Synology DS923+",
    "Bộ lưu điện APC Smart-UPS 1500VA",
    "Ổ cứng lưu trữ mạng Seagate IronWolf 8TB",
    "Máy chiếu Epson EB-FH52",
    "Máy chiếu BenQ MH560",
    "Màn chiếu treo tường Dalite 120 inch",
    "Màn hình tương tác ViewSonic IFP6550",
    "Bộ thiết bị hội nghị Logitech Rally",
    "Loa hội trường JBL EON715",
    "Micro không dây Shure BLX288",
    "Amply hội trường Yamaha PX3",
    "Camera trình chiếu vật thể Epson ELPDC21",
    "Bảng tương tác thông minh BenQ RM6503",
    "Bộ điều khiển trình chiếu Logitech R500",
    "Máy tính bảng Samsung Galaxy Tab S9 FE",
    "Máy ghi âm kỹ thuật số Sony ICD-UX570",
    "Tai nghe phòng ngoại ngữ Jabra Evolve2 40",
    "Webcam hội nghị Logitech Brio 4K",
    "Bộ thu phát tín hiệu HDMI không dây",
    "Máy hủy tài liệu văn phòng Fellowes 225Mi",
    "Máy chấm công vân tay Ronald Jack X628C",
    "Máy tính để bàn Acer Veriton X",
    "Máy tính xách tay ASUS ExpertBook B1",
    "Màn hình LG 27MP400 27 inch",
    "Máy in đa chức năng Brother MFC-L2701DW",
    "Máy quét mã vạch Honeywell Voyager 1250g",
    "Tủ hồ sơ sắt Hòa Phát TU09K7",
    "Bàn làm việc văn phòng Hòa Phát ET1400",
    "Ghế xoay lưới văn phòng lưng cao",
    "Máy điều hòa Daikin Inverter 18000 BTU",
    "Quạt đứng công nghiệp Senko DR1608",
    "Máy lọc nước RO Karofi KAD-D66",
    "Tủ lạnh bảo quản mẫu Panasonic NR-BV320",
    "Cân điện tử phòng thí nghiệm Sartorius Entris II",
    "Kính hiển vi quang học Olympus CX23",
    "Bộ cảm biến nhiệt độ và độ ẩm kỹ thuật số",
    "Bộ dụng cụ thí nghiệm vật lý cơ bản",
    "Máy đo pH để bàn Hanna HI2211",
    "Máy khuấy từ gia nhiệt IKA C-MAG HS 7",
    "Tủ hút khí độc phòng thí nghiệm 1200 mm",
    "Bộ nguồn DC phòng thực hành 30V 5A",
    "Kính hiển vi soi nổi Nikon SMZ-745",
    "Máy ly tâm phòng thí nghiệm Eppendorf 5702",
    "Bộ mô hình giải phẫu cơ thể người",
    "Bộ thí nghiệm quang học vật lý",
    "Bộ thí nghiệm điện tử cơ bản",
    "Giá sách thư viện thép 5 tầng",
    "Bàn đọc sách thư viện đôi",
    "Máy quét sách A3 Plustek OpticBook",
    "Máy tính tra cứu thư viện HP Pro Mini",
    "Cổng từ an ninh thư viện 2 cánh",
    "Máy đọc mã vạch thư viện Zebra DS2208",
    "Xe đẩy sách thư viện 3 tầng",
    "Bàn ghế phòng học sinh viên",
    "Bảng từ trắng di động 120 x 240 cm",
)

REPAIR_STATUSES = (
    "completed",
    "completed",
    "completed",
    "completed",
    "completed",
    "pending",
    "pending",
    "pending",
    "pending",
    "pending",
    "pending",
    "in_progress",
    "in_progress",
    "in_progress",
    "in_progress",
    "in_progress",
    "in_progress",
)


def add_assets_to_120() -> dict[str, int]:
    """Add missing assets and evenly distribute them among four workflows."""
    app = create_app()
    if make_url(app.config["SQLALCHEMY_DATABASE_URI"]).get_backend_name() != "sqlite":
        raise RuntimeError("Asset seeding is restricted to SQLite.")
    if len(ASSET_NAMES) != TARGET_ASSET_COUNT - 51:
        raise RuntimeError("The asset list must match the expected 69 new records.")

    inserted = {"assets": 0, "inventory": 0, "transfers": 0, "repairs": 0, "disposals": 0}
    with app.app_context():
        categories = Category.query.order_by(Category.id).all()
        departments = Department.query.order_by(Department.id).all()
        if len(categories) < 4 or len(departments) != 4:
            raise RuntimeError("Expected at least four categories and exactly four departments.")

        try:
            assets_by_code = {
                asset.asset_code: asset
                for asset in Asset.query.filter(
                    Asset.asset_code.in_(
                        [f"TS-{number:04d}" for number in range(51, 120)]
                    )
                ).all()
            }
            new_assets = []
            for index, name in enumerate(ASSET_NAMES):
                asset_code = f"TS-{index + 51:04d}"
                asset = assets_by_code.get(asset_code)
                if asset is None:
                    category = categories[index % len(categories)]
                    department = departments[index % len(departments)]
                    purchase_year = 2019 + index % 7
                    asset = Asset(
                        asset_code=asset_code,
                        name=name,
                        category=category,
                        department=department,
                        purchase_date=date(purchase_year, index % 12 + 1, index % 27 + 1),
                        useful_life_years=(
                            5 if category.name == "Thiết bị CNTT" else 8
                        ),
                        value=(
                            4_000_000
                            + (index % 10) * 1_250_000
                            + (index // 10) * 500_000
                        ),
                        status="active",
                        location=department.name,
                    )
                    db.session.add(asset)
                    inserted["assets"] += 1
                new_assets.append(asset)
            db.session.flush()

            inventory_assets = new_assets[:17]
            transfer_assets = new_assets[17:34]
            repair_assets = new_assets[34:51]
            disposal_assets = new_assets[51:]

            campaign_name = "Kiểm kê bổ sung tài sản năm 2026"
            campaign = Inventory.query.filter_by(name=campaign_name).first()
            if campaign is None:
                campaign = Inventory(
                    name=campaign_name,
                    start_date=date.today(),
                    status="pending",
                    created_by="Quản lý tài sản",
                )
                db.session.add(campaign)
                db.session.flush()
                campaign.details = [
                    InventoryDetail(
                        asset=asset,
                        expected_status=asset.status,
                        expected_location=asset.location,
                    )
                    for asset in inventory_assets
                ]
                inserted["inventory"] = len(inventory_assets)
            else:
                existing_ids = {
                    detail.asset_id
                    for detail in InventoryDetail.query.filter_by(
                        inventory_id=campaign.id
                    ).all()
                }
                missing_inventory_assets = [
                    asset for asset in inventory_assets if asset.id not in existing_ids
                ]
                campaign.details.extend(
                    InventoryDetail(
                        asset=asset,
                        expected_status=asset.status,
                        expected_location=asset.location,
                    )
                    for asset in missing_inventory_assets
                )
                inserted["inventory"] = len(missing_inventory_assets)

            for index, asset in enumerate(transfer_assets):
                reason = "Điều chuyển theo nhu cầu sử dụng giữa các phòng ban"
                if not Transfer.query.filter_by(asset_id=asset.id, reason=reason).first():
                    source = asset.department
                    destination = departments[
                        (departments.index(source) + 1) % len(departments)
                    ]
                    db.session.add(
                        Transfer(
                            asset=asset,
                            from_department=source,
                            to_department=destination,
                            transfer_date=date.today() - timedelta(days=17 - index),
                            reason=reason,
                            notes="Bàn giao thiết bị cho đơn vị tiếp nhận.",
                            performed_by="Cán bộ quản lý tài sản",
                        )
                    )
                    asset.department = destination
                    asset.location = destination.name
                    inserted["transfers"] += 1

            for index, asset in enumerate(repair_assets):
                description = f"Kiểm tra và bảo dưỡng định kỳ: {asset.name}"
                if not Repair.query.filter_by(
                    asset_id=asset.id, description=description
                ).first():
                    status = REPAIR_STATUSES[index]
                    request_date = date.today() - timedelta(days=20 - index)
                    db.session.add(
                        Repair(
                            asset=asset,
                            request_date=request_date,
                            repair_date=(
                                request_date + timedelta(days=2)
                                if status == "completed"
                                else None
                            ),
                            status=status,
                            description=description,
                            cost=350_000 + index * 75_000,
                            notes="Bảo dưỡng thiết bị và kiểm tra khả năng vận hành.",
                            requested_by="Nhân viên phụ trách thiết bị",
                            updated_by="Kỹ thuật viên",
                        )
                    )
                    if status in {"pending", "in_progress"}:
                        asset.status = "repair"
                    inserted["repairs"] += 1

            for index, asset in enumerate(disposal_assets):
                reason = "Đề nghị thanh lý do thiết bị cũ, hiệu suất sử dụng thấp"
                if not Disposal.query.filter_by(asset_id=asset.id, reason=reason).first():
                    db.session.add(
                        Disposal(
                            asset=asset,
                            disposal_date=date.today() + timedelta(days=30),
                            reason=reason,
                            liquidation_value=max(100_000, asset.value * 0.1),
                            status="requested",
                            requested_by="Cán bộ phụ trách tài sản",
                        )
                    )
                    inserted["disposals"] += 1

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        totals = {
            "assets": Asset.query.count(),
            "inventory": InventoryDetail.query.filter_by(
                inventory_id=campaign.id
            ).count(),
            "transfers": Transfer.query.count(),
            "repairs": Repair.query.count(),
            "disposals": Disposal.query.count(),
        }
        if totals["assets"] != TARGET_ASSET_COUNT:
            raise RuntimeError(
                f"Expected exactly {TARGET_ASSET_COUNT} assets, found {totals['assets']}."
            )
        return inserted


def main() -> None:
    result = add_assets_to_120()
    print("Asset expansion complete.")
    for kind, count in result.items():
        print(f"{kind}_inserted={count}")


if __name__ == "__main__":
    main()
