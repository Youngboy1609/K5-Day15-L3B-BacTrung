(reviewSelector = ".product-ratings") => {
    const text = element => (element?.innerText || "").trim();
    const fold = value => value.normalize("NFD").replace(/\p{M}/gu, "").replace(/đ/gi, "d").toLowerCase();
    const all = (root, selector) => Array.from(root?.querySelectorAll(selector) || []);
    const heading = document.querySelector("h1");
    const card = heading?.closest("section.card, [data-testid='product-detail']");
    if (!heading || !card) return null;
    const info = Array.from(card.children).find(child => child.contains(heading));
    const gallery = Array.from(card.children).find(child => info && child !== info && child.querySelector("img"));
    const img = el => el.getAttribute("data-src") || el.getAttribute("src") || el.currentSrc;
    const videos = el => all(el, "video, video source").map(v => v.currentSrc || v.src);
    const sections = all(document, ".page-product__detail h2, .product-detail h2, section h2");
    const section = label => sections.find(h => fold(text(h)) === label)?.closest("section");
    const details = section("chi tiet san pham");
    const description = section("mo ta san pham");
    const attributes = [], categories = [];
    for (const label of all(details, "h3,dt")) {
        const name = text(label);
        if (fold(name) === "danh muc") {
            for (const a of all(label.parentElement, "a[href]")) {
                const match = a.pathname.match(/-cat\.(?:\d+\.)*(\d+)\/?$/);
                if (match && text(a)) categories.push({category_id: match[1], name: text(a)});
            }
        } else {
            const value = Array.from(label.parentElement.children).filter(e => e !== label).map(text).filter(Boolean).join(" ");
            if (name && value) attributes.push({name, value});
        }
    }
    const tiers = [];
    for (const h of all(info, "h2")) {
        const buttons = all(h.parentElement, "button[class*='selection-box'],button[aria-pressed],button[role='radio']");
        const options = buttons.map(b => text(b) || b.getAttribute("aria-label")).filter(Boolean);
        if (options.length) tiers.push({name: text(h), options});
    }
    const shop = all(document, "a[href]").find(e => fold(text(e)) === "xem shop");
    const shopPanel = shop?.parentElement?.parentElement;
    const shopName = text(shopPanel?.firstElementChild).split("\n")[0];
    const summary = text(info).slice(text(info).indexOf(text(heading)) + text(heading).length);
    const rating = summary.match(/^\s*([0-5](?:[.,]\d+)?)\s+([\d.,]+[kKmM+]*)\s+đánh giá/i);
    const sold = summary.match(/(?:đã bán\s*([\d.,]+[km]?\+?)|([\d.,]+[km]?\+?)\s*đã bán)/i);
    const priceBox = all(info, "section[aria-live], [data-testid='product-price']").find(
        el => /₫/.test(text(el)) && !/phí ship/i.test(text(el)));
    const ogImage = document.querySelector('meta[property="og:image"]')?.content;
    const images = all(gallery, "picture img").filter(e => {
        const thumb = e.closest("picture")?.parentElement?.parentElement;
        return !thumb?.querySelector('img[alt*="video" i]');
    }).map(img);
    const reviewWidget = document.querySelector(reviewSelector || ".product-ratings");
    const pager = reviewWidget?.querySelector(".shopee-page-controller");
    const active = pager?.querySelector("button.shopee-button-solid--primary,button[aria-current='page']");
    const pageNumber = el => /^\d+$/.test(text(el)) ? Number(text(el)) : null;
    const buttons = all(pager, "button");
    const labels = buttons.filter(b => text(b));
    const reviewFilter = reviewWidget?.querySelector(".product-rating-overview__filter--active");
    const reviews = all(reviewWidget, "[data-cmtid]").map(row => {
        const media = row.querySelector(".rating-media-list");
        const pictures = all(media, ".rating-media-list__image-wrapper").filter(
            e => !e.querySelector("video,[class*='video'],img[alt*='video' i]"));
        const time = text(row.querySelector(".shopee-product-rating__time,.XYk98l")).split("|")[0].trim();
        const like = text(row.querySelector(".shopee-product-rating__like-count,[data-testid='review-like-count']"));
        const dislike = text(row.querySelector("[data-testid='review-dislike-count']"));
        return {id: row.dataset.cmtid, time, like, dislike,
            reply: text(row.querySelector(".shopee-product-rating__reply-content,[data-testid='seller-reply-content']")),
            images: pictures.flatMap(e => all(e, "picture img").map(img)),
            videos: videos(media), comment: text(row.querySelector(".YNedDV,.shopee-product-rating__content"))};
    });
    return {url: location.href, name: text(heading), shop_name: shopName,
        shop_username: shop?.pathname.match(/^\/([^/]+)\/?$/)?.[1], categories, attributes, tiers,
        description: description ? Array.from(description.children).filter(e => !e.matches("h2")).map(text).filter(Boolean).join("\n") : null,
        description_section_seen: Boolean(description), description_images: all(description, "img").map(img),
        gallery_images: images, cover: ogImage, videos: videos(gallery),
        price_text: text(priceBox), rating: rating?.[1], rating_count_display: rating?.[2],
        sold_display: sold?.[0], reviews, review_page: pageNumber(active), review_filter: fold(text(reviewFilter)),
        last_number_displayed: labels.length > 1 && labels[labels.length - 1] === active,
        page_buttons: buttons.filter(b => !b.disabled && b.getAttribute("aria-disabled") !== "true").map(pageNumber).filter(Boolean)};
}
