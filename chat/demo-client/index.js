//connects to socket.io server on localhost:3000
const socket = io("http://localhost:3000");

//displays a meesage in the chat
function addMessage(text, fromWho){
    const li = document.createElement("li");
    li.textContent = `${fromWho}: ${text}`;
    li.style.padding = "4px 8px";
    li.style.borderBottom = "1px solid #eee";
    document.getElementById("messages").appendChild(li);
}

socket.on("connect", () => {
    console.log("connected!");
    console.log("my socket id is:", socket.id);

//shows user they're connected and with what id
    addMessage(`you connected as ${socket.id}`, "system");
});

//event occurs either right after the first connection or when anyone send a message
socket.on("message", (data) => {
    console.log("server says:", data);

    //shows meesage in chat window
    addMessage(data,"server");

});

//for when the user types and send a message
//shows it in chatbox and sends to server to show others
document.getElementById("sendBtn").addEventListener("click",() =>{
    const input = document.getElementById("msgInput");
    const text = input.value.trim();

    //doesn't allow to send empty messages
    if (!text) return;


//adds messages to own chat called "me"
    addMessage(text, "me");
//text is send to server as "message" event
    socket.emit("message", text);
});
