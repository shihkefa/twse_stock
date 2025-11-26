import logging
from datetime import timedelta, datetime
import aiohttp
import async_timeout
import ssl
import certifi

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)
CURRENCY_TWD = "TWD"
POINTS = "points"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up TWSE stock sensors from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    stocks = entry.data.get("stocks", [])

    # 第一次強制刷新
    await coordinator.async_config_entry_first_refresh()

    entities = [TWSEStockSensor(coordinator, stock) for stock in stocks]
    async_add_entities(entities)


# ---------------------------------------------------------
#   Coordinator：抓全部股票資料
# ---------------------------------------------------------
class TWSECoordinator(DataUpdateCoordinator):
    """Coordinator: 依序抓取 TWSE 個股 / 大盤資料"""

    def __init__(self, hass, stocks):
        super().__init__(
            hass,
            _LOGGER,
            name="TWSE Stock Coordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.stocks = [s.strip() for s in stocks]

    async def _async_update_data(self):
        """抓取 TWSE MIS API 資料（不驗證 SSL）"""

        results = {}

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/117.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/javascript,*/*;q=0.01",
            "Referer": "https://mis.twse.com.tw/",
        }

        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            ) as session:

                for stock in self.stocks:
                    stock_code = stock.strip().lower()
                    if stock_code == "tw00":
                        stock_code = "t00"

                    url = (
                        "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
                        f"?ex_ch=tse_{stock_code}.tw&json=1&delay=0"
                    )

                    async with async_timeout.timeout(10):
                        resp = await session.get(url, headers=headers)

                        if resp.status != 200:
                            _LOGGER.warning("TWSE HTTP %s for %s", resp.status, stock)
                            results[stock] = None
                            continue

                        try:
                            data = await resp.json(content_type=None)
                        except Exception:
                            text = await resp.text()
                            _LOGGER.error(
                                "TWSE JSON decode error (%s): %s", stock, text[:150]
                            )
                            results[stock] = None
                            continue

                        msg_array = data.get("msgArray", [])
                        results[stock] = msg_array[0] if msg_array else None

        except Exception as err:
            raise UpdateFailed(f"TWSE fetch failed: {err}") from err

        return results


# ---------------------------------------------------------
#   個別 Sensor
# ---------------------------------------------------------
class TWSEStockSensor(CoordinatorEntity, SensorEntity):
    """單一股票或大盤 Sensor。"""

    def __init__(self, coordinator, stock):
        super().__init__(coordinator)

        self._stock = stock.strip().lower()
        self._coordinator = coordinator

        # 用來儲存前一次成功取得的價格
        self._last_value = None

        self._attr_name = f"{stock.upper()} 股價"
        self._attr_unique_id = f"twse_stock_{stock.lower()}"

        # 大盤顯示 points，個股用 TWD
        if self._stock == "t00":
            self._attr_native_unit_of_measurement = POINTS
        else:
            self._attr_native_unit_of_measurement = CURRENCY_TWD

    @property
    def available(self):
        return (
            self._coordinator.data is not None
            and self._stock in self._coordinator.data
            and self._coordinator.data[self._stock] is not None
        )

    @property
    def native_value(self):
        """主狀態：股價"""
        item = self._coordinator.data.get(self._stock)

        # 無資料 → 用最後值
        if not item:
            return self._last_value or "更新中"

        # ---------------------------
        # tw00：維持原邏輯
        # ---------------------------
        if self._stock == "t00":
            z_value = item.get("z")
            if z_value and z_value != "-":
                try:
                    self._last_value = float(z_value)
                except:
                    pass
            return self._last_value or "更新中"

        # ---------------------------
        # 個股邏輯（依照你的最終需求）
        # ---------------------------
        z_value = item.get("z")

        # ✔ Z 有值 → 使用 Z
        if z_value and z_value != "-":
            try:
                self._last_value = float(z_value)
                return self._last_value
            except:
                pass

        # ✔ Z 沒值 → 沒抓過 → 顯示 “更新中”
        if self._last_value is None:
            return "更新中"

        # ✔ Z 沒值 → 有抓過 → 維持前次值
        return self._last_value

    @property
    def extra_state_attributes(self):
        item = self._coordinator.data.get(self._stock)
        if not item:
            return {}

        return {
            "name": item.get("n") or item.get("c"),
            "open": item.get("o"),
            "high": item.get("h"),
            "low": item.get("l"),
            "volume": item.get("v") or item.get("m"),
            "trade_time": item.get("t"),
            "yesterday_close": item.get("y"),
            "change": item.get("d"),
            "change_percent": item.get("p"),
            "last_value": self._last_value,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @property
    def should_poll(self):
        return False
