"""Create a synthetic, relational demo dataset in a brand-new database."""

from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

from app.models import (
    Asset,
    Category,
    Department,
    Disposal,
    Inventory,
    InventoryDetail,
    InventoryObservation,
    Repair,
    Transfer,
    User,
    db,
)

DEMO_MARKER = "[DỮ LIỆU MẪU]"

CATEGORY_SPECS = (
    ("Máy tính và thiết bị ngoại vi", "Máy tính, máy in và thiết bị làm việc."),
    ("Thiết bị giảng dạy", "Thiết bị hỗ trợ giảng dạy và học tập."),
    ("Nội thất", "Bàn ghế, tủ và nội thất trường học."),
    ("Thiết bị mạng", "Hạ tầng mạng và thiết bị kết nối."),
    ("Thiết bị văn phòng", "Thiết bị dùng trong các phòng chức năng."),
)

DEPARTMENT_SPECS = (
    ("Ban Giám hiệu", "DEMO-BGH", "Văn phòng điều hành mẫu."),
    ("Phòng Công nghệ thông tin", "DEMO-CNTT", "Đơn vị công nghệ mẫu."),
    ("Phòng Kế toán", "DEMO-KT", "Đơn vị tài chính mẫu."),
    ("Thư viện", "DEMO-TV", "Không gian học tập mẫu."),
)

EMPLOYEE_SPECS = (
    ("demo_nhanvien_01", "Nguyễn An Bình"),
    ("demo_nhanvien_02", "Trần Minh Châu"),
    ("demo_nhanvien_03", "Lê Thu Hà"),
    ("demo_nhanvien_04", "Phạm Gia Huy"),
)

ASSET_NAMES = (
    ("Laptop Dell Latitude", "Máy tính để bàn HP ProDesk", "Màn hình Dell 24 inch",
     "Máy in Canon imageCLASS", "Máy quét tài liệu Epson", "Máy tính bảng Samsung"),
    ("Máy chiếu Epson", "Màn hình tương tác ViewSonic", "Bộ âm thanh lớp học",
     "Camera vật thể Aver", "Bộ thí nghiệm khoa học", "Bảng điện tử"),
    ("Bàn làm việc", "Ghế văn phòng", "Bàn học sinh đôi",
     "Tủ hồ sơ sắt", "Bảng trắng di động", "Giá sách thư viện"),
    ("Bộ chuyển mạch 24 cổng", "Bộ định tuyến Wi-Fi", "Bộ phát Wi-Fi",
     "Tủ rack mạng", "Bộ lưu điện UPS", "Thiết bị tường lửa"),
    ("Máy photocopy Ricoh", "Máy hủy tài liệu", "Máy chấm công",
     "Máy đóng gáy sách", "Điện thoại bàn", "Máy chiếu phòng họp"),
)


def seed_demo_data() -> None:
    """Insert synthetic records once; callers must verify the database is fresh."""
    today = date.today()
    now = datetime.now().replace(microsecond=0)

    try:
        categories = [
            Category(name=name, description=f"{DEMO_MARKER} {description}")
            for name, description in CATEGORY_SPECS
        ]
        departments = [
            Department(
                name=name,
                code=code,
                description=f"{DEMO_MARKER} {description}",
            )
            for name, code, description in DEPARTMENT_SPECS
        ]
        employees = [
            User(
                username=username,
                email=f"{username}@example.invalid",
                full_name=name,
                role="staff",
                is_active=False,
                password_hash=generate_password_hash(secrets.token_urlsafe(32)),
            )
            for username, name in EMPLOYEE_SPECS
        ]
        db.session.add_all([*categories, *departments, *employees])
        db.session.flush()

        assets = []
        employee_names = [employee.full_name for employee in employees]
        for category_index, names in enumerate(ASSET_NAMES):
            for item_index, name in enumerate(names):
                asset_index = category_index * len(names) + item_index
                assets.append(
                    Asset(
                        asset_code=f"DEMO-{asset_index + 1:03}",
                        name=name,
                        category=categories[category_index],
                        department=departments[asset_index % len(departments)],
                        user_name=employee_names[asset_index % len(employee_names)],
                        purchase_date=today - timedelta(days=180 + asset_index * 37),
                        useful_life_years=5 + asset_index % 6,
                        value=1_500_000 + asset_index * 475_000,
                        status="active",
                        location=(
                            f"Tầng {asset_index % 3 + 1}, "
                            f"phòng {asset_index % 12 + 1:02}"
                        ),
                        notes=f"{DEMO_MARKER} Tài sản hư cấu để hướng dẫn sử dụng.",
                    )
                )
        db.session.add_all(assets)
        db.session.flush()

        for index, asset in enumerate(assets[:4]):
            source = asset.department
            destination = departments[(departments.index(source) + 1) % len(departments)]
            db.session.add(
                Transfer(
                    asset=asset,
                    from_department=source,
                    to_department=destination,
                    transfer_date=today - timedelta(days=index + 2),
                    reason=f"{DEMO_MARKER} Điều chuyển minh họa.",
                    notes=f"{DEMO_MARKER} Lịch sử không đại diện cho tài sản thật.",
                    performed_by=employee_names[index],
                )
            )
            asset.department = destination

        repair_specs = (
            (4, "pending"),
            (5, "in_progress"),
            (6, "completed"),
        )
        for index, status in repair_specs:
            asset = assets[index]
            request_date = today - timedelta(days=12 - index)
            db.session.add(
                Repair(
                    asset=asset,
                    request_date=request_date,
                    repair_date=request_date + timedelta(days=2)
                    if status == "completed"
                    else None,
                    status=status,
                    description=f"{DEMO_MARKER} Yêu cầu kiểm tra thiết bị.",
                    cost=250_000 + index * 75_000,
                    notes=f"{DEMO_MARKER} Phiếu sửa chữa minh họa.",
                    requested_by=employee_names[index % len(employees)],
                    updated_by=employee_names[(index + 1) % len(employees)],
                )
            )
            if status in {"pending", "in_progress"}:
                asset.status = "repair"

        disposal_specs = ((7, "requested"), (8, "rejected"), (9, "approved"))
        for index, status in disposal_specs:
            db.session.add(
                Disposal(
                    asset=assets[index],
                    disposal_date=today + timedelta(days=30),
                    reason=f"{DEMO_MARKER} Đề nghị thanh lý minh họa.",
                    liquidation_value=100_000 + index * 25_000,
                    status=status,
                    requested_by=employee_names[index % len(employees)],
                    decided_by="Quản trị viên mẫu"
                    if status in {"approved", "rejected"}
                    else None,
                    decided_at=now if status in {"approved", "rejected"} else None,
                )
            )
            if status == "approved":
                assets[index].status = "disposal"

        inventory = Inventory(
            name=f"{DEMO_MARKER} Kiểm kê đầu kỳ",
            start_date=today - timedelta(days=1),
            status="pending",
            created_by=employee_names[0],
        )
        inventory.details = [
            InventoryDetail(
                asset=asset,
                expected_status=asset.status,
                expected_location=asset.location,
            )
            for asset in assets
            if asset.status != "disposal"
        ]
        db.session.add(inventory)
        db.session.flush()

        for index, detail in enumerate(inventory.details[:6]):
            if index == 4:
                detail.actual_status = "damaged"
            elif index == 5:
                detail.actual_status = "missing"
            else:
                detail.actual_status = detail.expected_status
            detail.actual_location = (
                None if detail.actual_status == "missing" else detail.expected_location
            )
            detail.variance_note = (
                f"{DEMO_MARKER} Ghi nhận minh họa."
                if detail.actual_status != detail.expected_status
                else f"{DEMO_MARKER} Đã kiểm đếm mẫu."
            )
            detail.checked_by = employee_names[index % len(employees)]
            detail.checked_at = now - timedelta(minutes=index)

        inventory.observations.append(
            InventoryObservation(
                observed_code="DEMO-OBS-001",
                observed_name=f"{DEMO_MARKER} Thiết bị chưa có trong danh mục",
                actual_status="active",
                note=f"{DEMO_MARKER} Ghi nhận tài sản ngoài danh mục để minh họa.",
                checked_by=employee_names[0],
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
