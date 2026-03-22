import frappe


def _set_agent_presence(is_live: int, status: str) -> None:
    user = frappe.session.user
    if not user or user == "Guest":
        return

    logger = frappe.logger("helpdesk.agent_presence")

    agent = frappe.db.get_value("HD Agent", {"user": user}, "name")
    if not agent:
        logger.info("No HD Agent found for user %s", user)
        return

    frappe.db.set_value(
        "HD Agent",
        agent,
        {
            "custom_is_live": is_live,
            "custom_status": status,
        },
        update_modified=False,
    )
    frappe.db.commit()
    logger.info("Set HD Agent %s (%s) -> %s", agent, user, status)


def on_login(login_manager):
    _set_agent_presence(1, "Online")


def on_logout(login_manager):
    _set_agent_presence(0, "Offline")