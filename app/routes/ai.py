"""AI assistant routes."""

import json
import os
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request

from app.llm.llm_service import LLMService
from app.models import Asset, Department, Disposal, Inventory, Repair, db
from app.rag.document_chunker import DocumentChunker
from app.rag.document_loader import DocumentLoader
from app.rag.rag_service import RAGService
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore
from app.routes.auth import login_required

bp = Blueprint("ai", __name__)


def build_rag_service():
    """Create a RAG service backed by school-asset documents."""
    documents_dir = Path(__file__).resolve().parents[1] / "data" / "documents"
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
    llm_service = LLMService(api_key=os.getenv("LLM_API_KEY"))
    return RAGService(Retriever(vector_store), llm_service)


def _safe_llm_generate(prompt):
    """Run the LLM only when a real API key exists; otherwise return a safe message."""
    llm_service = LLMService(api_key=os.getenv("LLM_API_KEY"))
    if not llm_service._has_valid_key():
        return "Không thể tạo phân tích AI vì API key chưa được cấu hình. Hệ thống vẫn đang hiển thị dữ liệu thống kê thực tế từ cơ sở dữ liệu."
    return llm_service.generate(prompt)


def _report_stats(report_type):
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
        rows = (
            db.session.query(Department.name, db.func.count(Asset.id).label("count"), db.func.coalesce(db.func.sum(Asset.value), 0).label("value"))
            .outerjoin(Asset, Asset.department_id == Department.id)
            .group_by(Department.id, Department.name)
            .order_by(db.func.count(Asset.id).desc())
            .all()
        )
        return {"department_summary": [{"name": row[0], "count": row[1], "value": float(row[2] or 0)} for row in rows]}
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
        rows = Inventory.query.order_by(Inventory.id.desc()).all()
        return {
            "inventory_rounds": [{
                "id": row.id,
                "name": row.name,
                "status": row.status,
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
            } for row in rows]
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
    except Exception as exc:
        return jsonify({"message": "AI API lỗi hoặc timeout. Vui lòng thử lại sau."}), 500


@bp.route("/ai/report", methods=["GET", "POST"])
@login_required
def report():
    """Generate a real database-backed report and optional AI analysis."""
    if request.method == "GET":
        return render_template("ai/report.html")

    payload = request.get_json(silent=True) or {}
    report_type = (payload.get("report_type") or "overview").strip() or "overview"
    stats = _report_stats(report_type)

    if report_type not in {"overview", "department", "repair", "disposal", "inventory"}:
        return jsonify({"message": "Loại báo cáo không hợp lệ."}), 400

    prompt = (
        "Bạn là trợ lý AI của trường học. Chỉ phân tích dữ liệu thống kê thực tế dưới đây. "
        "Không bịa thêm số liệu và không thêm dữ liệu không có trong JSON.\n\n"
        f"Dữ liệu thống kê thực tế: {json.dumps(stats, ensure_ascii=False, indent=2)}\n\n"
        "Hãy trả lời bằng tiếng Việt với các phần: 1) Tóm tắt ngắn, 2) Điểm đáng chú ý, 3) Gợi ý hành động."
    )

    try:
        analysis = _safe_llm_generate(prompt)
    except Exception:
        analysis = "Hệ thống AI hiện đang không thể tạo phân tích tự động vì API lỗi hoặc timeout. Dữ liệu thống kê thực tế vẫn được hiển thị phía trên để người dùng theo dõi."

    return jsonify({"report_type": report_type, "stats": stats, "analysis": analysis})
