
// chrome.browserAction.onClicked.addListener(function(tab) {

// 	chrome.tabs.executeScript({
// 		file: "/content-script.js"
//   	});
// });

chrome.browserAction.onClicked.addListener(function (tab) {
    chrome.tabs.executeScript({
        file: '/jquery.js'
    }, function() {
        // Guaranteed to execute only after the previous script returns
        chrome.tabs.executeScript({
            file: '/content-script.js'
        });
    });
});