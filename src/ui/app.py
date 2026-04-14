"""Calvados Science Assistance UI (Streamlit).

UI uses backend API endpoints (same endpoints as n8n).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import requests
import streamlit as st


DEFAULT_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
AGENT_ENDPOINTS = {
    "text-analysis": "/agent/text-analysis",
    "requirement-analysis": "/agent/requirement-analysis",
    "structure": "/agent/structure",
    "generation": "/agent/generation",
    "recommendation": "/agent/recommendation",
    "scoring": "/agent/scoring",
    "compliance": "/agent/compliance",
    "report": "/agent/report",
}
CHAT_AGENT_NAMES = list(AGENT_ENDPOINTS.keys())


def _init_state() -> None:
    st.session_state.setdefault("api_url", DEFAULT_API_URL)
    st.session_state.setdefault("token", "")
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("last_file_id", "")
    st.session_state.setdefault("last_agent_result", None)
    st.session_state.setdefault("last_chat_result", None)
    st.session_state.setdefault("ai_provider", "github")
    st.session_state.setdefault("ai_api_key", "")


def _headers() -> dict[str, str]:
    token = st.session_state.get("token", "").strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _api_request(
    method: str,
    path: str,
    *,
    json_payload: Optional[dict[str, Any]] = None,
    files: Optional[dict[str, Any]] = None,
    timeout: int = 90,
) -> tuple[bool, Any]:
    url = st.session_state["api_url"].rstrip("/") + path
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=_headers(),
            json=json_payload,
            files=files,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return False, {"error": f"API connection error: {exc}"}

    content_type = (response.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        body = response.json()
    else:
        body = response.text
    if response.status_code >= 400:
        return False, {"status_code": response.status_code, "body": body}
    return True, body


def _parse_json(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc


def _render_sidebar() -> None:
    st.sidebar.title("Calvados Science Assistance")
    st.sidebar.caption("UI for backend API + n8n-compatible agents")
    st.session_state["api_url"] = st.sidebar.text_input(
        "Backend API URL",
        value=st.session_state["api_url"],
        help="Example: http://localhost:8000",
    )

    if st.sidebar.button("Check backend health"):
        ok, data = _api_request("GET", "/health", timeout=20)
        if ok:
            st.sidebar.success("Backend is up")
            st.sidebar.json(data)
        else:
            st.sidebar.error("Backend is not reachable")
            st.sidebar.json(data)

    st.sidebar.markdown("---")
    st.sidebar.subheader("AI API Key")
    providers = ["github", "openai", "openrouter", "claude"]
    current_provider = st.session_state.get("ai_provider", "github")
    provider_index = providers.index(current_provider) if current_provider in providers else 0
    st.session_state["ai_provider"] = st.sidebar.selectbox(
        "Provider",
        options=providers,
        index=provider_index,
        help="Выберите провайдера для AI-рекомендаций",
    )
    api_key_input = st.sidebar.text_input(
        "API key (только для текущей сессии)",
        type="password",
        value=st.session_state.get("ai_api_key", ""),
    )
    connect_col, clear_col = st.sidebar.columns(2)
    with connect_col:
        if st.button("Connect key"):
            st.session_state["ai_api_key"] = api_key_input.strip()
    with clear_col:
        if st.button("Clear key"):
            st.session_state["ai_api_key"] = ""
    if st.session_state.get("ai_api_key"):
        st.sidebar.success(f"AI key connected ({st.session_state['ai_provider']})")
    else:
        st.sidebar.info("AI key не подключен: будет rule-based режим")

    user = st.session_state.get("user")
    if user:
        st.sidebar.success(f"Logged in as {user.get('email')}")
        if st.sidebar.button("Log out"):
            st.session_state["token"] = ""
            st.session_state["user"] = None
            st.rerun()
    else:
        st.sidebar.warning("Not authenticated")


def _render_auth_block() -> None:
    st.subheader("Authentication")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
        if submitted:
            ok, data = _api_request(
                "POST",
                "/auth/login",
                json_payload={"email": email, "password": password},
                timeout=30,
            )
            if ok:
                st.session_state["token"] = data["access_token"]
                st.session_state["user"] = data["user"]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Login failed")
                st.json(data)

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Name", key="reg_name", value="Hackathon User")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
            submitted = st.form_submit_button("Create account")
        if submitted:
            ok, data = _api_request(
                "POST",
                "/auth/register",
                json_payload={"name": name, "email": email, "password": password},
                timeout=30,
            )
            if ok:
                st.success("Account created, now log in.")
            else:
                st.error("Registration failed")
                st.json(data)


def _render_upload_and_agents() -> None:
    st.subheader("Upload document and run agents")
    st.info(
        "Порядок работы: 1) загрузите файл, 2) запустите нужные агенты (или весь pipeline через n8n), "
        "3) скачайте отчёт в MD/JSON/XLSX."
    )

    uploaded = st.file_uploader("Upload PDF/DOCX/TXT", type=["pdf", "docx", "txt"])
    if uploaded and st.button("Upload file"):
        file_obj = {
            "file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream"),
        }
        ok, data = _api_request("POST", "/api/upload", files=file_obj)
        if ok:
            st.success("File uploaded")
            st.session_state["last_file_id"] = data["file_id"]
            st.json(data)
        else:
            st.error("Upload failed")
            st.json(data)

    file_id = st.text_input(
        "file_id (for agent calls)",
        value=st.session_state.get("last_file_id", ""),
        key="agent_file_id",
    )
    selected_agent = st.selectbox("Agent", options=list(AGENT_ENDPOINTS.keys()), index=0)
    direct_text = st.text_area(
        "Optional raw text (if set, file_id is optional)",
        height=120,
        placeholder="You can pass text directly to an agent...",
    )
    context_raw = st.text_area(
        "Optional context JSON",
        value="{}",
        height=120,
    )

    if st.button("Run selected agent"):
        try:
            context = _parse_json(context_raw)
        except ValueError as exc:
            st.error(str(exc))
            return
        context = _with_ai_context(context)

        payload: dict[str, Any] = {"context": context}
        if file_id.strip():
            payload["file_id"] = file_id.strip()
        if direct_text.strip():
            payload["text"] = direct_text.strip()

        ok, data = _api_request("POST", AGENT_ENDPOINTS[selected_agent], json_payload=payload)
        if ok:
            st.success(f"Agent '{selected_agent}' executed")
            st.session_state["last_agent_result"] = data
            if selected_agent == "recommendation":
                _render_recommendation_transparency(data)
            st.json(data)
        else:
            st.error("Agent call failed")
            st.json(data)

    if st.session_state.get("last_agent_result") is not None:
        with st.expander("Last agent result", expanded=False):
            st.json(st.session_state["last_agent_result"])

    if file_id.strip():
        st.markdown("### Download latest report")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Download report (md)"):
                ok, resp = _download_report(file_id.strip(), "md")
                if ok:
                    st.download_button(
                        label="Save report.md",
                        data=resp["content"],
                        file_name=resp["filename"],
                        mime="text/markdown",
                    )
                else:
                    st.error("Download failed")
                    st.json(resp)
        with col2:
            if st.button("Download report (json)"):
                ok, resp = _download_report(file_id.strip(), "json")
                if ok:
                    st.download_button(
                        label="Save report.json",
                        data=resp["content"],
                        file_name=resp["filename"],
                        mime="application/json",
                    )
                else:
                    st.error("Download failed")
                    st.json(resp)
        with col3:
            if st.button("Download report (xlsx template)"):
                ok, resp = _download_report(file_id.strip(), "xlsx")
                if ok:
                    st.download_button(
                        label="Save report.xlsx",
                        data=resp["content"],
                        file_name=resp["filename"],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                else:
                    st.error("Download failed")
                    st.json(resp)


def _download_report(file_id: str, fmt: str) -> tuple[bool, dict[str, Any]]:
    url = st.session_state["api_url"].rstrip("/") + f"/api/report/{file_id}/download?format={fmt}"
    try:
        response = requests.get(url, headers=_headers(), timeout=60)
    except requests.RequestException as exc:
        return False, {"error": str(exc)}
    if response.status_code >= 400:
        payload = response.text
        try:
            payload = response.json()
        except Exception:
            pass
        return False, {"status_code": response.status_code, "body": payload}
    filename = f"report.{fmt}"
    disposition = response.headers.get("content-disposition", "")
    if "filename=" in disposition:
        filename = disposition.split("filename=")[-1].strip().strip('"')
    return True, {"filename": filename, "content": response.content}


def _render_generation() -> None:
    st.subheader("Generate TZ draft")
    st.info("Рекомендуется указывать file_id: генератор сохранит смысл исходного ТЗ и заполнит шаблонный формат.")
    with st.form("generation_form"):
        source_file_id = st.text_input("Source file_id (recommended)", value=st.session_state.get("last_file_id", ""))
        project_title = st.text_input("Project title", value="Scientific R&D Program Draft")
        priority = st.text_input("Priority", value="Energy, advanced materials and transport")
        specialization = st.text_input("Specialization", value="AI and digital energy")
        budget_total = st.text_input("Total budget", value="1 500 000 тыс. тенге")
        years = st.text_input("Years (comma-separated)", value="2026,2027,2028")
        yearly_budget = st.text_input("Per-year budget", value="500 000 тыс. тенге")
        submitted = st.form_submit_button("Generate")

    if submitted:
        payload = {
            "context": _with_ai_context({}),
            "file_id": source_file_id.strip() or None,
            "project_title": project_title,
            "priority": priority,
            "specialization": specialization,
            "budget_total": budget_total,
            "years": [item.strip() for item in years.split(",") if item.strip()],
            "year_budget": yearly_budget,
        }
        ok, data = _api_request("POST", "/agent/generation", json_payload=payload)
        if ok:
            st.success("Draft generated")
            result = data.get("result", {})
            st.text_area("Generated TZ", value=result.get("generated_text", ""), height=360)
            st.caption(
                f"Method: {result.get('generation_method', 'unknown')} · "
                f"Source length: {result.get('source_text_length', 0)}"
            )
            generated_file_id = (result.get("file_id") or source_file_id or "").strip()
            if generated_file_id:
                dl_ok, dl = _download_generated_docx(generated_file_id)
                if dl_ok:
                    st.download_button(
                        label="Download generated TZ (.docx)",
                        data=dl["content"],
                        file_name=dl["filename"],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    st.warning("DOCX not ready yet")
                    st.json(dl)
            st.json(data)
        else:
            st.error("Generation failed")
            st.json(data)


def _download_generated_docx(file_id: str) -> tuple[bool, dict[str, Any]]:
    url = st.session_state["api_url"].rstrip("/") + f"/api/generation/{file_id}/download"
    try:
        response = requests.get(url, headers=_headers(), timeout=60)
    except requests.RequestException as exc:
        return False, {"error": str(exc)}
    if response.status_code >= 400:
        payload = response.text
        try:
            payload = response.json()
        except Exception:
            pass
        return False, {"status_code": response.status_code, "body": payload}
    filename = "generated_tz.docx"
    disposition = response.headers.get("content-disposition", "")
    if "filename=" in disposition:
        filename = disposition.split("filename=")[-1].strip().strip('"')
    return True, {"filename": filename, "content": response.content}


def _render_history() -> None:
    st.subheader("Document history")
    if st.button("Refresh history"):
        pass
    ok, data = _api_request("GET", "/api/history", timeout=30)
    if not ok:
        st.error("Cannot load history")
        st.json(data)
        return

    items = data.get("items", [])
    if not items:
        st.info("History is empty")
        return

    st.dataframe(items, use_container_width=True)
    ids = [item["id"] for item in items]
    selected = st.selectbox("Select file_id for details", options=ids)
    if st.button("Load selected details"):
        ok, details = _api_request("GET", f"/api/history/{selected}", timeout=30)
        if ok:
            st.json(details)
        else:
            st.error("Cannot load details")
            st.json(details)


def _render_chat() -> None:
    st.subheader("AI chat")
    chat_agent = st.selectbox("Chat agent", options=CHAT_AGENT_NAMES, index=4)
    chat_file_id = st.text_input("Optional file_id", value=st.session_state.get("last_file_id", ""))
    message = st.text_area("Message", height=100)
    context_raw = st.text_area("Optional chat context JSON", value="{}", height=100, key="chat_context")

    if st.button("Send chat message"):
        if not message.strip():
            st.warning("Message is empty")
            return
        try:
            context = _parse_json(context_raw)
        except ValueError as exc:
            st.error(str(exc))
            return
        context = _with_ai_context(context)

        payload = {
            "message": message,
            "agent_name": chat_agent,
            "file_id": chat_file_id.strip() or None,
            "context": context,
        }
        ok, data = _api_request("POST", "/api/chat", json_payload=payload)
        if ok:
            st.session_state["last_chat_result"] = data
            st.success("Chat response received")
            st.json(data)
        else:
            st.error("Chat request failed")
            st.json(data)

    if st.button("Load chat history"):
        path = "/api/chat/history"
        if chat_file_id.strip():
            path += f"?file_id={chat_file_id.strip()}"
        ok, data = _api_request("GET", path, timeout=30)
        if ok:
            st.json(data)
        else:
            st.error("Cannot load chat history")
            st.json(data)


def _render_recommendation_transparency(api_response: dict[str, Any]) -> None:
    result = api_response.get("result") or {}
    transparency = result.get("transparency") or {}
    if not transparency:
        return

    quality = (transparency.get("text_quality") or {}).get("quality_flag", "unknown")
    confidence = transparency.get("analysis_confidence", "medium")
    text_length = transparency.get("text_length", 0)
    st.caption(
        f"Прозрачность анализа: quality={quality}, confidence={confidence}, text_length={text_length}"
    )
    for note in transparency.get("notes") or []:
        st.info(note)

    ai = result.get("ai_enhancement") or {}
    if ai.get("status") == "skipped" and ai.get("note"):
        st.warning(ai.get("note"))


def _with_ai_context(context: Optional[dict[str, Any]]) -> dict[str, Any]:
    merged = dict(context or {})
    ai_provider = (st.session_state.get("ai_provider") or "").strip()
    ai_api_key = (st.session_state.get("ai_api_key") or "").strip()
    if ai_provider:
        merged["ai_provider"] = ai_provider
    if ai_api_key:
        merged["ai_api_key"] = ai_api_key
    return merged


def main() -> None:
    st.set_page_config(page_title="Calvados Science Assistance", layout="wide")
    _init_state()
    _render_sidebar()

    st.title("Calvados Science Assistance")
    st.caption("Technical specification analysis platform (UI over backend API)")

    if not st.session_state.get("token"):
        _render_auth_block()
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Upload + Agents", "Generate TZ", "History", "Chat"],
    )
    with tab1:
        _render_upload_and_agents()
    with tab2:
        _render_generation()
    with tab3:
        _render_history()
    with tab4:
        _render_chat()


if __name__ == "__main__":
    main()
