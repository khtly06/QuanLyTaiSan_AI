"""AI assistant routes."""

import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, render_template, request

from app.llm.llm_service import LLMProviderError, LLMService
from app.models import (
    Asset,
    AIReport,
    Department,
    Disposal,
    Inventory,
    InventoryDetail,
    InventoryObservation,
    Repair,
    db,
)
from app.rag.document_chunker import DocumentChunker
from app.rag.document_loader import DocumentLoader
from app.rag.rag_service import RAGService
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore
from app.routes.auth import current_user, login_required

bp = Blueprint("ai", __name__)
logger = logging.getLogger(__name__)


def _create_llm_service():
    """Build the configured OpenAI-compatible LLM client."""
    return LLMService(
        api_key=current_app.config["LLM_API_KEY"],
        model=current_app.config["LLM_MODEL"],
        base_url=current_app.config["LLM_API_BASE_URL"],
        timeout=current_app.config["LLM_TIMEOUT_SECONDS"],
        max_prompt_chars=current_app.config["LLM_MAX_PROMPT_CHARS"],
    )


def build_rag_service():
    """Create a RAG service backed by school-asset documents."""
    documents_dir = Path(__file__).resolve().parents[2] / "data" / "documents"
    vector_store = VectorStore()
    chunker = DocumentChunker(chunk_size=400, chunk_overlap=60)
    documents = []

    if documents_dir.exists():
        for file_path in sorted(documents_dir.glob("*")):
            if file_path.suffix.lower() not in {".txt", ".md", ".markdown", ".pdf", ".docx"}:
                continue
            try:
                text = DocumentLoader(str(file_path)).load()
            except FileNotFoundError:
                continue
            documents.extend(chunker.chunk_text(text, file_path.name))

    if not documents:
        default_documents = [
            {
                "id": "policy_1",
                "source_name": "school_asset_policy.md",
                "content": (
                    "Quy định quản lý tài sản trường học: Tài sản cố định phải được ghi "
                    "nhận, kiểm kê định kỳ mỗi quý và phân công trách nhiệm cho từng bộ "
                    "phận. Mỗi tài sản phải có mã định danh rõ ràng và được cập nhật vào "
                    "hệ thống nếu có thay đổi trạng thái."
                ),
            },
            {
                "id": "policy_2",
                "source_name": "inventory_procedure.md",
                "content": (
                    "Quy trình kiểm kê tài sản: Ban giám hiệu lập kế hoạch kiểm kê, các bộ "
                    "phận thực hiện đối chiếu và xác minh, sau đó tổng hợp kết quả để xử lý "
                    "tài sản hỏng, thiếu, hoặc thừa."
                ),
            },
            {
                "id": "policy_3",
                "source_name": "disposal_rules.md",
                "content": (
                    "Tài sản hư hỏng hoặc hết hạn sử dụng phải được lập biên bản, xác định "
                    "giá trị thanh lý và được phê duyệt theo quy trình quản lý tài sản của "
                    "trường học."
                ),
            },
        ]
        documents = default_documents

    vector_store.add_documents(documents)
    llm_service = _create_llm_service()
    return RAGService(Retriever(vector_store), llm_service)


def _safe_llm_generate(prompt, system_prompt=None):
    """Run the configured LLM provider."""
    llm_service = _create_llm_service()
    response = llm_service.generate(prompt, system_prompt=system_prompt)
    try:
        parsed_response = json.loads(response)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The LLM provider returned invalid JSON.") from exc
    if not isinstance(parsed_response, dict) or not {
        "summary",
        "observations",
        "recommendations",
    }.issubset(parsed_response):
        raise RuntimeError("The LLM provider returned an unexpected report structure.")
    if (
        not isinstance(parsed_response["summary"], str)
        or not isinstance(parsed_response["observations"], list)
        or not isinstance(parsed_response["recommendations"], list)
        or not all(isinstance(item, str) for item in parsed_response["observations"])
        or not all(
            isinstance(item, str) for item in parsed_response["recommendations"]
        )
    ):
        raise RuntimeError("The LLM provider returned invalid report field types.")
    return json.dumps(parsed_response, ensure_ascii=False, indent=2)


def _report_stats(report_type, department_id=None, inventory_id=None):
    """Collect actual metrics from the database for AI reporting."""
    if report_type == "overview":
        return {
            "total_assets": Asset.query.count(),
            "active_assets": Asset.query.filter_by(status="active").count(),
            "repair_assets": Asset.query.filter_by(status="repair").count(),
            "disposal_assets": Asset.query.filter_by(status="disposal").count(),
            "total_value": float(db.session.query(db.func.coalesce(db.func.sum(Asset.value), 0)).scalar() or 0),
        }
    if report_type == "department":
        department = db.session.get(Department, department_id)
        if department is None:
            raise ValueError("Phòng ban không tồn tại.")
        assets = Asset.query.filter_by(department_id=department.id).all()
        if len(assets) > 100:
            raise ValueError(
                "Phòng ban có hơn 100 tài sản; hãy dùng báo cáo tổng quan để tránh gửi quá nhiều dữ liệu."
            )
        pending_disposal_ids = {
            asset_id
            for (asset_id,) in db.session.query(Disposal.asset_id)
            .filter(
                Disposal.status == "requested",
                Disposal.asset_id.in_([asset.id for asset in assets]),
            )
            .all()
        }
        status_counts = {
            "in_use": sum(asset.status == "active" for asset in assets),
            "damaged": sum(asset.status == "damaged" for asset in assets),
            "under_repair": sum(asset.status == "repair" for asset in assets),
            "pending_disposal": len(pending_disposal_ids),
        }
        return {
            "department": department.name,
            "asset_count": len(assets),
            "status_counts": status_counts,
            "total_value": float(sum(asset.value or 0 for asset in assets)),
            "assets": [
                {
                    "asset_code": asset.asset_code,
                    "name": asset.name,
                    "status": asset.status,
                    "location": asset.location,
                    "pending_disposal": asset.id in pending_disposal_ids,
                    "value": float(asset.value or 0),
                    "purchase_date": (
                        asset.purchase_date.isoformat() if asset.purchase_date else None
                    ),
                }
                for asset in assets
            ],
        }
    if report_type == "repair":
        rows = Repair.query.order_by(Repair.id.desc()).all()
        return {
            "repair_requests": [{
                "id": row.id,
                "asset_id": row.asset_id,
                "status": row.status,
                "description": row.description,
                "cost": float(row.cost or 0),
            } for row in rows]
        }
    if report_type == "disposal":
        rows = Disposal.query.order_by(Disposal.id.desc()).all()
        return {
            "disposals": [{
                "id": row.id,
                "asset_id": row.asset_id,
                "reason": row.reason,
                "status": row.status,
                "liquidation_value": float(row.liquidation_value or 0),
            } for row in rows]
        }
    if report_type == "inventory":
        inventory = db.session.get(Inventory, inventory_id)
        if inventory is None:
            raise ValueError("Đợt kiểm kê không tồn tại.")
        if inventory.status != "completed":
            raise ValueError("Chỉ có thể tạo báo cáo AI cho đợt kiểm kê đã hoàn thành.")
        details = (
            InventoryDetail.query.filter_by(inventory_id=inventory.id)
            .order_by(InventoryDetail.id)
            .all()
        )
        if len(details) > 100:
            raise ValueError(
                "Đợt có hơn 100 tài sản; báo cáo AI chi tiết bị giới hạn để bảo vệ dữ liệu và kích thước yêu cầu."
            )
        observations = InventoryObservation.query.filter_by(
            inventory_id=inventory.id
        ).order_by(InventoryObservation.id).all()
        checked = [detail for detail in details if detail.actual_status is not None]
        present = [detail for detail in checked if detail.actual_status != "missing"]
        missing = [detail for detail in checked if detail.actual_status == "missing"]
        damaged = [detail for detail in checked if detail.actual_status == "damaged"]
        repair_needed = [detail for detail in checked if detail.actual_status == "repair"]
        wrong_location = [
            detail
            for detail in checked
            if detail.expected_location
            and detail.actual_location
            and detail.expected_location.strip().casefold()
            != detail.actual_location.strip().casefold()
        ]

        def asset_entry(detail):
            is_wrong_location = detail in wrong_location
            classification = []
            if detail.actual_status != "missing":
                classification.append("accounted_for")
            if detail.actual_status == "missing":
                classification.append("missing")
            if detail.actual_status == "damaged":
                classification.append("damaged")
            if detail.actual_status == "repair":
                classification.append("needs_repair")
            if is_wrong_location:
                classification.append("wrong_location")
            if detail.actual_status != detail.expected_status:
                classification.append("status_mismatch")
            return {
                "asset_code": detail.asset.asset_code,
                "name": detail.asset.name,
                "expected_status": detail.expected_status,
                "actual_status": detail.actual_status,
                "expected_location": detail.expected_location,
                "actual_location": detail.actual_location,
                "note": detail.variance_note,
                "classification": classification,
            }

        return {
            "inventory_id": inventory.id,
            "name": inventory.name,
            "status": inventory.status,
            "expected_count": len(details),
            "checked_count": len(checked),
            "unverified_count": len(details) - len(checked),
            "confirmed_missing_count": len(missing),
            "damaged_or_repair_count": len(damaged) + len(repair_needed),
            "accounted_for_count": len(present),
            "missing_count": len(missing),
            "damaged_count": len(damaged),
            "needs_repair_count": len(repair_needed),
            "wrong_location_count": len(wrong_location),
            "location_not_recorded_count": sum(
                not detail.expected_location or not detail.actual_location
                for detail in checked
            ),
            "asset_results": [asset_entry(detail) for detail in checked],
            "unregistered_observations": [
                {
                    "observed_code": item.observed_code,
                    "observed_name": item.observed_name,
                    "actual_status": item.actual_status,
                    "note": item.note,
                    "checked_by": item.checked_by,
                    "checked_at": item.checked_at.isoformat(),
                }
                for item in observations
            ],
        }
    if report_type == "recommendations":
        department = db.session.get(Department, department_id)
        if department is None:
            raise ValueError("Vui lòng chọn phòng ban hợp lệ cho báo cáo gợi ý.")
        assets = (
            Asset.query.filter_by(department_id=department.id)
            .order_by(Asset.id)
            .all()
        )
        if len(assets) > 100:
            raise ValueError(
                "Phòng ban có hơn 100 tài sản; không thể tạo gợi ý trong giới hạn dữ liệu an toàn."
            )
        return {
            "department": department.name,
            "assets": [
                {
                    "asset_code": asset.asset_code,
                    "name": asset.name,
                    "department": asset.department.name if asset.department else None,
                    "status": asset.status,
                    "location": asset.location,
                    "purchase_date": (
                        asset.purchase_date.isoformat() if asset.purchase_date else None
                    ),
                    "age_years": (
                        max(0, (date.today() - asset.purchase_date).days // 365)
                        if asset.purchase_date
                        else None
                    ),
                    "useful_life_years": asset.useful_life_years,
                    "repair_count": len(asset.repairs),
                    "repair_history": [
                        {
                            "request_date": item.request_date.isoformat(),
                            "repair_date": (
                                item.repair_date.isoformat() if item.repair_date else None
                            ),
                            "status": item.status,
                            "description": item.description,
                            "cost": float(item.cost or 0),
                        }
                        for item in sorted(asset.repairs, key=lambda repair: repair.id)
                    ],
                }
                for asset in assets
            ]
        }
    return {} 


@bp.route("/ai/chat", methods=["GET", "POST"])
@login_required
def chat():
    """Handle AI questions for the school asset assistant."""
    if request.method == "GET":
        return render_template("ai/chatbot.html")

    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = {"question": request.form.get("question", "")}

    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"message": "Câu hỏi rỗng. Vui lòng nhập câu hỏi để trợ lý AI hỗ trợ."}), 400

    try:
        rag_service = build_rag_service()
        result = rag_service.answer_question(question)
        return jsonify({
            "answer": result["answer"],
            "sources": result["sources"],
            "question": question,
        })
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except LLMProviderError as exc:
        logger.warning("AI chat provider request failed: category=%s", exc.category)
        return jsonify({"message": exc.user_message}), 503
    except RuntimeError:
        logger.warning("LLM provider request failed while answering an AI chat question.")
        return jsonify({"message": "AI API lỗi hoặc timeout. Vui lòng thử lại sau."}), 500


@bp.route("/ai/report", methods=["GET", "POST"])
@login_required
def report():
    """Generate a real database-backed report and optional AI analysis."""
    if request.method == "GET":
        user = current_user()
        reports_query = AIReport.query.order_by(AIReport.created_at.desc())
        if not user.is_admin:
            reports_query = reports_query.filter_by(created_by_id=user.id)
        return render_template(
            "ai/report.html",
            departments=Department.query.order_by(Department.name).all(),
            inventory_rounds=Inventory.query.filter_by(status="completed")
            .order_by(Inventory.id.desc())
            .all(),
            is_admin=user.is_admin,
            saved_reports=reports_query.limit(10).all(),
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "Nội dung yêu cầu báo cáo phải là JSON hợp lệ."}), 400
    report_type = payload.get("report_type", "overview")
    if not isinstance(report_type, str):
        return jsonify({"message": "Loại báo cáo không hợp lệ."}), 400
    report_type = report_type.strip() or "overview"
    if report_type not in {
        "overview",
        "department",
        "repair",
        "disposal",
        "inventory",
        "recommendations",
    }:
        return jsonify({"message": "Loại báo cáo không hợp lệ."}), 400
    user = current_user()
    if report_type in {"inventory", "recommendations"} and not user.is_admin:
        return jsonify({"message": "Chỉ quản trị viên được tạo loại báo cáo này."}), 403

    try:
        department_id = (
            int(payload["department_id"])
            if payload.get("department_id") not in (None, "")
            else None
        )
        inventory_id = (
            int(payload["inventory_id"])
            if payload.get("inventory_id") not in (None, "")
            else None
        )
    except (TypeError, ValueError):
        return jsonify({"message": "Mã phòng ban hoặc đợt kiểm kê không hợp lệ."}), 400
    if report_type == "department" and department_id is None:
        return jsonify({"message": "Vui lòng chọn phòng ban."}), 400
    if report_type == "recommendations" and department_id is None:
        return jsonify({"message": "Vui lòng chọn phòng ban cho báo cáo gợi ý."}), 400
    if report_type == "inventory" and inventory_id is None:
        return jsonify({"message": "Vui lòng chọn đợt kiểm kê."}), 400

    try:
        stats = _report_stats(report_type, department_id, inventory_id)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    prompt_dir = Path(__file__).resolve().parents[2] / "prompts"
    system_prompt = (prompt_dir / "ai_report_system.md").read_text(encoding="utf-8")
    prompt_template = (prompt_dir / "ai_report_user.md").read_text(encoding="utf-8")
    prompt = prompt_template.replace("{{report_type}}", report_type).replace(
        "{{stats_json}}", json.dumps(stats, ensure_ascii=False, indent=2)
    )
    report_instructions = {
        "inventory": (
            "\n\nYÊU CẦU RIÊNG - BÁO CÁO KIỂM KÊ:\n"
            "Tóm tắt lần lượt tài sản đầy đủ/đã tìm thấy, tài sản thiếu đã được xác nhận, "
            "tài sản hỏng, tài sản sai vị trí (chỉ khi có đủ vị trí kỳ vọng và thực tế), "
            "tài sản cần sửa chữa, và đề xuất xử lý. Nêu số lượng và mã/tên tài sản "
            "dựa đúng asset_results và classification tương ứng trong dữ liệu. Nếu thiếu dữ liệu vị trí, "
            "nêu rõ và không kết luận sai vị trí. Kết luận là tham khảo để admin xem xét."
        ),
        "department": (
            "\n\nYÊU CẦU RIÊNG - TÓM TẮT THEO PHÒNG BAN:\n"
            "Tóm tắt tổng số tài sản, đang sử dụng, hỏng, đang sửa và chờ thanh lý "
            "theo status_counts. Không suy diễn tình trạng hỏng nếu dữ liệu không ghi nhận."
        ),
        "recommendations": (
            "\n\nYÊU CẦU RIÊNG - GỢI Ý SỬA CHỮA HOẶC THAY THẾ:\n"
            "Đánh giá riêng từng tài sản từ tuổi tài sản (age_years), thời gian sử dụng "
            "dự kiến (useful_life_years), số lần sửa chữa (repair_count), lịch sử sửa chữa "
            "và tình trạng. Phân loại đề xuất thành: nên tiếp tục sử dụng, nên sửa chữa, "
            "cần theo dõi, hoặc có khả năng cần thay thế. Mỗi đề xuất phải nêu mã tài sản "
            "và căn cứ dữ liệu. Nếu tuổi thọ dự kiến hoặc ngày mua chưa có, nói rõ dữ liệu "
            "thiếu; không tự đặt ngưỡng tuổi thọ. Đây chỉ là gợi ý để admin xem xét."
        ),
    }
    prompt += report_instructions.get(report_type, "")

    ai_generated = True
    try:
        analysis = _safe_llm_generate(prompt, system_prompt=system_prompt)
    except ValueError as exc:
        ai_generated = False
        logger.info("AI report was not sent because its prompt was rejected: %s", exc)
        analysis = (
            "Không thể gửi dữ liệu tới AI trong giới hạn đã cấu hình. "
            "Số liệu thực tế bên trên vẫn có thể được đối chiếu. "
            f"Chi tiết: {exc}"
        )
    except LLMProviderError as exc:
        ai_generated = False
        logger.warning("AI report provider request failed: category=%s", exc.category)
        analysis = (
            f"{exc.user_message} "
            "Số liệu thực tế bên trên vẫn có thể được đối chiếu."
        )
    except RuntimeError:
        ai_generated = False
        logger.warning("LLM provider request failed while generating an AI report.")
        analysis = "Hệ thống AI hiện đang không thể tạo phân tích tự động vì dịch vụ lỗi hoặc timeout. Dữ liệu thống kê thực tế vẫn được hiển thị phía trên để người dùng theo dõi."

    reference_label = {
        "inventory": "Kết quả AI – Tham khảo",
        "department": "Tham khảo",
        "recommendations": "Tham khảo",
    }.get(report_type)
    report_id = None
    if reference_label:
        scope_label = (
            stats["name"]
            if report_type == "inventory"
            else stats.get("department", "Toàn bộ tài sản")
        )
        saved_report = AIReport(
            report_type=report_type,
            scope_label=scope_label,
            stats_json=json.dumps(stats, ensure_ascii=False),
            analysis=analysis,
            reference_label=reference_label,
            status="pending" if ai_generated else "unavailable",
            ai_generated=ai_generated,
            created_by_id=user.id,
        )
        db.session.add(saved_report)
        db.session.commit()
        report_id = saved_report.id
    return jsonify({
        "report_type": report_type,
        "stats": stats,
        "analysis": analysis,
        "reference_label": reference_label,
        "report_id": report_id,
        "review_status": "pending" if ai_generated and report_id else "unavailable",
    })


@bp.route("/ai/report-records/<int:report_id>", methods=["GET"])
@login_required
def get_ai_report_record(report_id):
    """Return a saved report to its creator or an administrator."""
    user = current_user()
    report = db.session.get(AIReport, report_id)
    if report is None or (
        not user.is_admin and report.created_by_id != user.id
    ):
        abort(404)
    return jsonify({
        "report_id": report.id,
        "report_type": report.report_type,
        "scope_label": report.scope_label,
        "stats": json.loads(report.stats_json),
        "analysis": report.analysis,
        "reference_label": report.reference_label,
        "review_status": report.status,
        "ai_generated": report.ai_generated,
        "created_by": report.created_by.full_name or report.created_by.username,
        "created_at": report.created_at.isoformat(),
        "decided_by": (
            report.decided_by.full_name or report.decided_by.username
            if report.decided_by
            else None
        ),
        "decided_at": report.decided_at.isoformat() if report.decided_at else None,
        "can_decide": user.is_admin and report.status == "pending",
    })


@bp.route("/ai/report-records/<int:report_id>/decision", methods=["POST"])
@login_required
def decide_ai_report(report_id):
    """Record an administrator's review without changing asset records."""
    user = current_user()
    if not user.is_admin:
        abort(403)
    report = db.session.get(AIReport, report_id)
    if report is None:
        abort(404)
    if report.status != "pending" or not report.ai_generated:
        return jsonify({"message": "Báo cáo này không còn chờ phê duyệt."}), 409

    payload = request.get_json(silent=True)
    decision = payload.get("decision") if isinstance(payload, dict) else None
    if decision not in {"approved", "rejected"}:
        return jsonify({"message": "Quyết định báo cáo không hợp lệ."}), 400

    report.status = decision
    report.decided_by_id = user.id
    report.decided_at = datetime.now(UTC).replace(tzinfo=None)
    db.session.commit()
    return jsonify({
        "report_id": report.id,
        "review_status": report.status,
        "decided_by": user.full_name or user.username,
        "decided_at": report.decided_at.isoformat(),
    })
