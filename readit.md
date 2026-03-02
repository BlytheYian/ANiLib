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

container 預設只會管「左右的寬度與對齊」

rounded-4:
border-radius: var(--bs-border-radius-xl); /* 換算成像素大約是 1rem(字體大小) 或 16px */
rounded-circle	50%	變成正圓形（適合使用者頭像）
rounded-pill	50rem	變成膠囊狀（適合導覽列按鈕）

Bootstrap 的間距 class 命名邏輯超級直覺，完全是縮寫組成的：

第一碼 (屬性)：m 代表 Margin (外邊距，推開別人)，p 代表 Padding (內邊距，把自己的肚子撐大)。

第二碼 (方向)：t (Top 上)、b (Bottom 下)、s (Start 左)、e (End 右)、x (左右水平)、y (上下垂直)。

第三碼 (大小)：數字 0 到 5，數字越大距離越寬。

所以 mt-4 的意思就是：Margin Top 大小為 4。

ratio-1x1：正方形 (適合大頭貼)

ratio-4x3：傳統電視比例 (微扁)

ratio-16x9：YouTube 影片標準比例 (適合橫式劇照)

ratio-21x9：電影寬螢幕比例

ratio-3x4 或手動寫 CSS aspect-ratio: 3/4;：最適合動漫、電影海報的直式長方形！

1. 斷點切換原理：navbar-expand-lg
Bootstrap 的 Navbar 之所以能「大螢幕橫排、小螢幕收折」，全靠最外層的 navbar-expand-lg 這個類別。

lg (Large) 的意義：它代表螢幕寬度大於 992px（通常是平板橫向或電腦螢幕）。

大於 992px 時：Bootstrap 會強制把裡面帶有 collapse 的區塊展開，變成橫向排列。

小於 992px 時：Bootstrap 會把 collapse 區塊隱藏起來。這時，必須點擊那個帶有 data-bs-toggle="collapse" 的漢堡按鈕，它才會往下展開。

2. 排版推擠魔法：me-auto 與 ms-auto
這是現代網頁排版（CSS Flexbox）最神妙的技巧。在 Flex 容器裡，margin: auto 會像「彈簧」一樣把元素推開。

me-auto (Margin End Auto)：我加在「動畫庫」的外層 <ul> 上。這代表它的右邊會有一個無限大的彈簧，把它右邊所有的東西（搜尋框、按鈕）全部用力推到畫面最右側。

ms-auto (Margin Start Auto)：我加在「搜尋框與按鈕」的外層 <div> 上。這代表它的左邊有彈簧，確保這組功能區塊永遠貼著右邊界。

因為這兩個彈簧的作用，畫面就完美切成了三等份：「Logo (靠左) --- 動畫庫 (跟著 Logo) ===== 彈簧空間 ===== 搜尋與按鈕 (靠右)」。

@ 符號在 CSS 裡叫做 At-rule（At-規則）。

你可以把它想像成 CSS 裡的 「特殊指令」 或 「條件判斷」。一般的 CSS 是直接寫「誰（選擇器）要長什麼樣」，而開頭帶有 @ 的指令，則是在跟瀏覽器溝通「環境」或「行為」。
/* 當螢幕寬度「至少」有 992px 時才執行括號內的樣式 */
@media (min-width: 992px) {
    .navbar-collapse {
        display: flex !important; /* 電腦版：讓選單現身 */
    }
}
@media,處理不同螢幕尺寸,變形金剛：依環境改變外觀
@keyframes,定義動畫過程,劇本：定義 0% 到 100% 要演什麼
@font-face,載入自定義字體,搬運工：從伺服器把漂亮字體搬過來
@import,引入另一個 CSS 檔案,外掛：把別人的規則書插進來用