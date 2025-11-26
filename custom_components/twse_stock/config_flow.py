import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class TWSEStockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """TWSE 股票監控 Config Flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # user_input["stocks"] 可以是逗號分隔字串
            # 轉成 list 儲存
            stocks_str = user_input.get("stocks", "")
            stocks_list = [s.strip() for s in stocks_str.split(",") if s.strip()]
            return self.async_create_entry(
                title="TWSE 股票監控",
                data={"stocks": stocks_list}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("stocks", default=""): str
            }),
            errors=errors,
        )
