function httpGetAsync(url, callback) {
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.open("GET", "messages", url, true);
  xmlHttp.onreadystatechange = function() {
    if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
      callback(xmlHttp.responseText);
      getMessages(xmlHttp.responseText);
    }
  }
  xmlHttp.send(null);
}
function httpPostAsync(method, params, callback) {
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.onreadystatechange = function() {
    if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
      callback(xmlHttp.responseText);
    else
      callback(`Error ${xmlHttp.status}`)
  }
  xmlHttp.open("POST", window.location.href + method, true);
  xmlHttp.setRequestHeader("Content-Type", "application/json");
  xmlHttp.send(params);
}
let message = [];
const form = document.querySelector('.message-form');
form.addEventListener('submit', event => {
    event.preventDefault();
    const input = document.querySelector('.typedMessage');
    const text = input.value.trim();
    if(text !== '') {
        httpPostAsync("message", JSON.stringify({"message":text}), function(){});
        addMessage(text);
        input.value = '';
        input.focus();
    }
});
function addMessage(text) {
    const chat = {
        text,
        id: Date.now()
    }
    message.push(chat);
    const list = document.querySelector('.messages');
    list.insertAdjacentHTML('beforeend',
        `<p class="userMessage-item" data-key="${chat.id}">
            <span>${chat.text}</span>
        </p>`
    );
}
function addPartnerMessage(text) {
  var textArr = text.split('PADDING');
  console.log(textArr);
  for(var i = 0; i < textArr.length; i++) {
    var mes = textArr[i];
    console.log(mes);
    const chat = {
        text: mes,
        id: Date.now()
    }
    message.push(chat);
    const list = document.querySelector('.messages');
    list.insertAdjacentHTML('beforeend',
        `<p class="partnerMessage-item" data-key="${chat.id}">
            <span>${chat.text}</span>
        </p>`
    );
  }
}
function getMessages(text) {
  if (new String(text).valueOf() != new String("None").valueOf()) {
    addPartnerMessage(text);
  }
}
setInterval(() => httpGetAsync("http://localhost:8080", function(){}), 1000);
