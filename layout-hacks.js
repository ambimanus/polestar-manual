window.hack_injectcss = function(cssrule) {
    document.styleSheets[0].insertRule(`${cssrule}`, 0);
}

window.hack_carmodel = function() {
    const selector = "#root > div.css-1q8magb > div.css-yp9swi > section:nth-child(2) > div > div.css-h3768a > div.css-zlttcb > div.css-uu17cs > button > div > div.css-qzsukn";
    return document.querySelector(selector).textContent;
}

window.hack_remove_elems = async function(elems) {
    let errors = [];
    for (const elem of elems) {
        try {
            document.querySelector(`${elem}`).style.display="none";
        }
        catch(err) {
            errors.push(err)
        }
        await new Promise(r => setTimeout(r, 10));
    }
    if (errors.length > 0) {
        throw errors;
    }
}

window.hack_remove_unnecessary_toc_elems = function() {
    const inverse_selectors = [
        // header, footer and stuff around the main content
        "#root > div.css-1q8magb > :not(div.css-yp9swi)",
        // stuff besides the headline
        "#root > div.css-1q8magb > div.css-yp9swi > section[data-testid='main-tabs-view'] > div > :not(div[data-testid='menu-headline'])",
        // stuff besides the car model
        "#root > div.css-1q8magb > div.css-yp9swi > section[data-testid='owners-manual-view'] > div > div.css-h3768a > :not(div.css-zlttcb)",
        // stuff besides the owners-manual-accordion and the car model
        "#root > div.css-1q8magb > div.css-yp9swi > section[data-testid='owners-manual-view'] > div > :not(div.css-h3768a,div.css-1bto9ww,div[data-testid='owners-manual-accordion'])",
        // cookie banner
        "#onetrust-consent-sdk"
    ];
    for (const selector of inverse_selectors) {
        let elems = document.querySelectorAll(selector);
        for (const elem of elems) {
            elem.style.display="none";
        }
    }
}

window.hack_remove_unnecessary_chapter_elems = function() {
    // move article-content higher up in the DOM tree
    let el_article_content = document.querySelector('div[data-testid="article-content"]');
    let el_root_data = document.querySelector('#root > div.css-1q8magb');
    el_root_data.appendChild(el_article_content);
    // remove everything else
    let elems = document.querySelectorAll('#root > div.css-1q8magb > :not(div[data-testid="article-content"])');
    for (const elem of elems) {
        elem.style.display="none";
    }
    // cookie banner
    document.querySelector('#onetrust-consent-sdk').style.display="none";
}

window.hack_expand_sections = async function() {
    let aria_buttons = document.querySelectorAll('button[aria-expanded=\"false\"]');
    for (const aria_btn of aria_buttons) {
        aria_btn.click();
        await new Promise(r => setTimeout(r, 10));
    }
}

window.hack_scrape_links = function() {
    let x = hack_scrape_link_elems();
    let myarray = []
    for (var i = 0; i < x.length; i++) {
            let nametext = x[i].textContent;
            let cleantext = nametext.replace(/\s+/g, ' ').trim();
            let cleanlink = x[i].href;
            myarray.push([cleantext, cleanlink]);
    };
    return myarray;
}

window.hack_scrape_link_elems = function() {
    return document.querySelectorAll("a.css-1l08h8j");
}

window.hack_scrape_hierarchy = function() {
    let tocitems = [];
    let tocelems = document.querySelectorAll("div.css-yof1vp h1,div.css-yof1vp label,div.css-yof1vp div.css-15kwtnw");
    let section = null;
    let subsection = null;
    for (const elem of tocelems) {
        console.log(elem.tagName, elem.textContent);
        if (elem.tagName.toLowerCase() == 'h1') {
            section = {text: elem.textContent, subsections: []};
            tocitems.push(section);
        }
        if (elem.tagName.toLowerCase() == 'label') {
            subsection = {text: elem.textContent, items: []};
            section.subsections.push(subsection);
        }
        if (elem.tagName.toLowerCase() == 'div') {
            subsection.items.push(elem.textContent);
        }
    }
    return tocitems;
}