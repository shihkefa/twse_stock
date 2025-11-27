# twse_stock
TWSE台股股價接入Homeassistant

是透過台灣證券交易所公開的接口將資料導入

支持上市以及上櫃股票代號

例如大盤指數代號t00

接口網址:https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_t00.tw&json=1&delay=0

抓取Z欄位內容值接入HA狀態(下圖紅框標示)

大盤顯示單位points;個股顯示單位TWD

只要這個接口可以查詢到的股票代號，就沒有問題

開啟接口網址後，修改t00(下圖紅框標示)成其他股票代號如果可以查詢到，就可以接入。

 <img src="https://github.com/shihkefa/twse_stock/blob/main/API.png?raw=true" width="800">

在HA中可以一次新增一檔股票，或是一次新增多檔，一次新增多檔在輸入股票代號的時候用逗號隔開即可(例:0050,00919,00713)

 <img src="https://github.com/shihkefa/twse_stock/blob/main/input.png?raw=true" width="300">

