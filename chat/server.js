const { createServer } = require("http");
const { Server } = require("socket.io");

//creates http server
const httpServer = createServer();

const io = new Server(httpServer, {
  cors: {
    origin: "http://127.0.0.1:5500", 
  },
});


//runs every time a clinet connects
io.on("connection", (socket) => {
  console.log("client connected:", socket.id);

  //listens for messages from this specific client
socket.on("message", (data) => {
    console.log("client said:", data);
//allows all connected clients to see the message
//added socket id to knoow who sent it
    io.emit("message", `${socket.id}: ${data}`);
  });
 

  socket.emit("message", "Hello");
});
//starts server on port 3000
httpServer.listen(3000, () => {
  console.log("Server is connected on port 3000");
});
