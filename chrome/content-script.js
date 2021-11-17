// var divs = document.getElementById("header-author");

var old_comments = document.getElementsByClassName('fivetagsloc');
for (var j = 0; j < old_comments.length; j++) {

    old_comments[j].removeChild(old_comments[j].lastChild);
}



var c_id = document.getElementsByClassName("yt-simple-endpoint style-scope yt-formatted-string")
var temp = [];

for (i=0;i<c_id.length;i++){
    var href = c_id[i].href;
    var loc = href.search("lc=")
    if (loc!= -1){
        var ccid =href.substring(loc+3,loc+29) 
        temp[temp.length] = ccid;
    }
}
var cid_list=[]
for (i=0;i<temp.length;i++){
    if (i%2==0){
        cid_list[cid_list.length]=temp[i]
    }
}

var data={"url":window.location.href,"cid_list":cid_list};




var div_ls = document.getElementsByTagName('div')
for(var i=0;i<div_ls.length;i++){
    // 遍历所有的div并根据id做判断
    if(div_ls[i].getAttribute('id') == 'header-author'){
        // 对满足条件的标签设置属性即可
        div_ls[i].setAttribute('class', 'fivetagsloc')
    }
}

var divs = document.getElementById("container");

var comments = document.getElementsByClassName('fivetagsloc');




// for (var j = 0; j < comments.length; j++) {
    
//     var div = document.createElement("div");
//     comments[j].appendChild(div);


 
//     //yt
//     var img = document.createElement("img");
//     img.setAttribute("id", "newImg");
//     img.setAttribute("class", "yt");
//     //like
//     // img.src = "https://i.imgur.com/qk812Yw.png";
//     //non
//     // img.src = "https://i.imgur.com/JH8jk3S.png";
//     //unlike
//     img.src = "https://i.imgur.com/tmz24ir.png";
//     img.width="20";
//     img.style.float='left';
//     img.style.margin='5px';
//     div.appendChild(img);


//     //video
//     var img = document.createElement("img");
//     img.setAttribute("id", "newImg");
//     img.setAttribute("class", "yt");
//     //like
//     // img.src = "https://i.imgur.com/0iMhDq2.png";
//     //non
//     // img.src = "https://i.imgur.com/jls9Rx0.png";
//     //unlike
//     img.src = "https://i.imgur.com/xHj6D9z.png";
//     img.width="20";
//     img.style.float='left';
//     img.style.margin='5px';
//     div.appendChild(img);


//     //excited
//     var img = document.createElement("img");
//     img.setAttribute("id", "newImg");
//     img.setAttribute("class", "yt");
//     //1
//     // img.src = "https://i.imgur.com/dfBtV31.png";
//     //2
//     // img.src = "https://i.imgur.com/EJCDN9A.png";
//     // //3
//     // img.src = "https://i.imgur.com/hA3Zbd6.png";
//     // //4
//     // img.src = "https://i.imgur.com/MzLVfu5.png";
//     //5
//     img.src = "https://i.imgur.com/utRzdId.png";
//     img.width="20";
//     img.style.float='left';
//     img.style.margin='5px';
//     div.appendChild(img);


//     //irony
//     var img = document.createElement("img");
//     img.setAttribute("id", "newImg");
//     img.setAttribute("class", "irony");
//     img.src = "https://i.imgur.com/YgjdqzW.png";
//     img.width="20";
//     img.style.float='left';
//     img.style.margin='5px';
//     div.appendChild(img);


//     //sex
//     var img = document.createElement("img");
//     img.setAttribute("id", "newImg");
//     img.setAttribute("class", "sex");
//     img.src = "https://i.imgur.com/qk812Yw.png";
//     img.width="20";
//     img.style.float='left';
//     img.style.margin='5px';
//     div.appendChild(img);


  
    
// }

$.ajax({
   url: 'https://81ab6a05c623.ngrok.io/test',
   type: 'POST',
   data:JSON.stringify(data),
   dataType: 'json',

   success: function (response) {
        for (var i = 0; i < comments.length; i++) {
            var div = document.createElement("div");
            div.setAttribute("class", "fivetags");

            comments[i].appendChild(div);


            //yt
            var img = document.createElement("img");
            img.setAttribute("id", "newImg");
            img.setAttribute("class", "yt");
            if (response[cid_list[i]]['yter'] ==1){
                //like
                img.src = "https://i.imgur.com/ezppPhH.png";
            }
            else if (response[cid_list[i]]['yter'] ==2){
                //non
                img.src = "https://i.imgur.com/JH8jk3S.png";
            }
            else if (response[cid_list[i]]['yter'] ==3){
                //unlike
                img.src = "https://i.imgur.com/tmz24ir.png";
            }
            else{
       
                var txt=document.createElement("p");
                txt.innerHTML="此留言尚未進行分析"; 
                div.appendChild(txt);
            }
            img.width="20";
            img.style.float='left';
            img.style.margin='5px';
            div.appendChild(img);



            //video
            var img = document.createElement("img");
            img.setAttribute("id", "newImg");
            img.setAttribute("class", "v");
            if (response[cid_list[i]]['v'] ==1){
                //like
                img.src = "https://i.imgur.com/0iMhDq2.png";
            }
            else if (response[cid_list[i]]['v'] ==2){
                //non
                img.src = "https://i.imgur.com/jls9Rx0.png";
            }
            else if (response[cid_list[i]]['v'] ==3){
                //unlike
                img.src = "https://i.imgur.com/xHj6D9z.png";
            }
            img.width="20";
            img.style.float='left';
            img.style.margin='5px';
            div.appendChild(img);




            //excited
            var img = document.createElement("img");
            img.setAttribute("id", "newImg");
            img.setAttribute("class", "ex");
            if (response[cid_list[i]]['ex'] ==1){
                //1
                img.src = "https://i.imgur.com/dfBtV31.png";
            }
            else if (response[cid_list[i]]['ex'] ==2){
                //2
                img.src = "https://i.imgur.com/EJCDN9A.png";
            }
            else if (response[cid_list[i]]['ex'] ==3){
                //3
                img.src = "https://i.imgur.com/hA3Zbd6.png";
            }
            else if (response[cid_list[i]]['ex'] ==4){
                //4
                img.src = "https://i.imgur.com/MzLVfu5.png";
            }
            else if (response[cid_list[i]]['ex'] ==5){
                //5
                img.src = "https://i.imgur.com/utRzdId.png";
            }
            img.width="20";
            img.style.float='left';
            img.style.margin='5px';
            div.appendChild(img);



            //irony
            var img = document.createElement("img");
            img.setAttribute("id", "newImg");
            img.setAttribute("class", "irony");
            img.src = "https://i.imgur.com/YgjdqzW.png";
            img.width="20";
            img.style.float='left';
            img.style.margin='5px';
            if (response[cid_list[i]]['ir'] ==2){
                div.appendChild(img);
            }
            


            //sex
            var img = document.createElement("img");
            img.setAttribute("id", "newImg");
            img.setAttribute("class", "sex");
            img.src = "https://i.imgur.com/qk812Yw.png";
            img.width="20";
            img.style.float='left';
            img.style.margin='5px';
            if (response[cid_list[i]]['se'] ==2){
                div.appendChild(img);
            }

        }

   },
   error: function (error) {
       console.log(error);
   }
});



    


// alert(window.location.href);


// var data={"url":window.location.href};



// $.ajax({
//    url: 'https://51f7de3b48ca.ngrok.io/test',
//    type: 'POST',
//    data:data,
//    dataType: 'json',
//    // headers: {'Access-Control-Allow-Origin': '*'},
//    success: function (response) {
//        alert(response['cid_list']);
//        var cid = response['cid_list'];
//        alert(cid);
//    },
//    error: function (error) {
//        console.log(error);
//    }
// });



