python manage.py makemigrations
python manage.py migrate
python manage.py runserver


boostrap
1. 骨架：
網格系統 (Grid System)這是 Bootstrap 最核心的功能，用來決定東西怎麼擺。.
container：最外層的袋子，負責把內容鎖在螢幕中間，不讓它貼邊。
.row：一排。所有的內容都必須放在「排」裡面。.col：直欄。Bootstrap 把一排分成 12 格。
col-6：佔一半寬度。col-md-4：在電腦版（Medium 以上）佔 $1/3$ 寬度 ($12 \div 4 = 3$)。

2. 工具：
通用類別 (Utilities)這是一群「小標籤」，讓你不用寫 CSS 就能改外觀。它們通常是縮寫：
間距 (Spacing)：m- (Margin, 外距), p- (Padding, 內距)。
mt-3：上方外距 (Margin Top) 給 3 號單位的空間。
mx-auto：左右置中。
彈性佈局 (Flexbox)：
d-flex：把容器變成彈性盒子。
justify-content-center：裡面的東西「水平置中」。
align-items-center：裡面的東西「垂直置中」。
顯示控制：
d-none：隱藏。
d-md-block：在電腦版才顯示。

3. 組件：
預製套裝 (Components)這是 Bootstrap 幫你寫好的大塊積木。
.card：一個帶邊框和陰影的盒子。
.carousel：一個會動的投影片。
.btn：一個漂亮的按鈕。
.badge：一顆小標籤（如「熱門」、「2024」）。

4. 靈魂：
Data Attributes (數據屬性)這是你剛剛「按鈕沒反應」的關鍵！Bootstrap 的 JavaScript 插件不需要你寫 JS，它是靠 HTML 標籤裡的 data-bs-* 來連動的。
data-bs-ride="carousel"：告訴 JS「這個東西要自動開始跑」。
data-bs-target="#myID"：告訴按鈕「你要控制哪一個 ID 的物件」。
data-bs-slide="next"：告訴按鈕「點我時要切換到下一張」。為什麼你的箭頭會沒反應？通常是因為按鈕上的 data-bs-target="#A" 和最外層的 id="B" 對不起來。就像你的遙控器對準了隔壁家的電視，當然轉不了台。

ani_index.html
<!-- forloop.counter0: 從 0 開始數, .counter從1 , 類似於i++-->
<!-- 這是頁面一開始的渲染, 之後js每5秒移動一次.active到下個頁面 -->
<!-- 預設的 .carousel-item：CSS 是 display: none;（完全隱藏）。加上 .active 後：CSS 變成 display: block;（顯示出來）。 -->
<!-- aria: 無障礙設計, 用來告知"當前項目" -->

rounded-4:
border-radius: var(--bs-border-radius-xl); /* 換算成像素大約是 1rem(字體大小) 或 16px */
rounded-circle	50%	變成正圓形（適合使用者頭像）
rounded-pill	50rem	變成膠囊狀（適合導覽列按鈕）