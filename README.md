# twse_stock
TWSE台股股價接入Homeassistant

是透過台灣證券交易所公開的接口將資料導入

例如大牌指數代號t00

接口網址:https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_t00.tw&json=1&delay=0

抓取Z欄位內容值接入HA狀態

大盤顯示單位points;個股顯示單位TWD

只要這個接口可以查詢到的股票代號，就可以接入

網址中的t00更改成其他股票代號如果可以查詢到，就可以接入。


 <img src="https://github.com/shihkefa/twse_stock/blob/main/API.png?raw=true" width="800">


