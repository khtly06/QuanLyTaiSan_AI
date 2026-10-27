"""Tests for safe category and department CRUD."""

from app.models import Category, Department


def test_category_duplicate_and_in_use_delete_are_rejected(app, authenticated_client):
    duplicate = authenticated_client.post(
        "/categories", data={"name": "Thiết bị"}
    )
    delete_used = authenticated_client.post("/categories/1/delete")

    assert duplicate.status_code == 400
    assert delete_used.status_code == 400
    with app.app_context():
        assert Category.query.count() == 1
        assert Category.query.one().name == "Thiết bị"


def test_category_can_be_edited_and_unused_category_deleted(
    app, authenticated_client
):
    created = authenticated_client.post("/categories", data={"name": "Phụ kiện"})
    assert created.status_code == 302
    with app.app_context():
        category_id = Category.query.filter_by(name="Phụ kiện").one().id

    updated = authenticated_client.post(
        f"/categories/{category_id}/edit",
        data={"name": "Phụ kiện máy tính", "description": "Mô tả"},
    )
    assert updated.status_code == 302
    deleted = authenticated_client.post(f"/categories/{category_id}/delete")

    assert deleted.status_code == 302
    with app.app_context():
        assert Category.query.filter_by(name="Phụ kiện máy tính").first() is None


def test_department_delete_rejects_referenced_department(app, authenticated_client):
    response = authenticated_client.post("/departments/1/delete")

    assert response.status_code == 400
    with app.app_context():
        assert Department.query.filter_by(code="A").one()


def test_department_update_rejects_duplicate_code(app, authenticated_client):
    created = authenticated_client.post(
        "/departments", data={"name": "Phòng C", "code": "C"}
    )
    assert created.status_code == 302
    with app.app_context():
        department_id = Department.query.filter_by(code="C").one().id

    response = authenticated_client.post(
        f"/departments/{department_id}/edit",
        data={"name": "Phòng C", "code": "A"},
    )

    assert response.status_code == 400
    with app.app_context():
        assert Department.query.filter_by(code="C").one()
