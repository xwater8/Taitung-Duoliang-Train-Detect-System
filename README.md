## Introduction
1. 可用來觀看youtube直播IPCamera部分, 看到變化比較大的擷取時間點
2. 可用來蒐集人形資料, 將來做裝備辨識可以使用
3. VideoDenoise, 有些IPCamera畫質比較差, 或許有機會用上
- 畫面中解碼有方塊
- 畫面中在晚上容易有噪點
- 玻璃上的反光去掉

## TODO:
- [] 使用Streamlink將Youtube串流變成rtsp服務, 方便持續進行分析
- [] 使用Background subtraction將前景移動的人物抓取下來
- [] 使用Temporal Noise Reductionz方法降低影片雜訊
- [] 將有物體移動的片段記錄下來存成圖片以及.csv紀錄時間
- [] 新增RoI排除指定區域


## 紀錄:
### 透過StreamLink將Youtube變成rtsp串流
```
#安裝streamlink
$sudo apt-get install streamlink

#將youtube透過streamlink變成串流服務
streamlink --stdout -4 "https://www.youtube.com/watch?v=UCG1aXVO8H8" best | ffmpeg -i pipe:0 -c copy -f rtsp rtsp://localhost:8554/stream

streamlink -4 --hls-live-edge 3 "https://www.youtube.com/watch?v=UCG1aXVO8H8" best

streamlink --stream-url "https://www.youtube.com/watch?v=UCG1aXVO8H8"

```

### 透過yt-dlp將Youtube變成rtsp串流
```

#嘗試使用yt-dlp
##透過yt-dlp獲取串流網址
$yt-dlp -g "https://www.youtube.com/watch?v=UCG1aXVO8H8"

會得到以下資訊

https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1759053394/ei/8rHYaLzmJvL0pt8PjP2G8Ao/ip/123.192.232.66/id/UCG1aXVO8H8.18/itag/96/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D137/rqh/1/hls_chunk_host/rr2---sn-3cgv-un5ez.googlevideo.com/xpc/EgVo2aDSNQ%3D%3D/playlist_duration/30/manifest_duration/30/bui/ATw7iSVenlYJTHYCuhAsyo9H-xhxZNugBCApC25ErF5UR0AtGRoPwktI7LWaMJG32kN9nhYohI1e06X8/spc/hcYD5ZeSr_Vj8AagNiVwMOy3gcyAYzDC3Ug0EaPk0cGx7PTQ1AUU8ah0j6fmmwWgbRI/vprv/1/playlist_type/DVR/initcwndbps/3726250/met/1759031794,/mh/zD/mm/44/mn/sn-3cgv-un5ez/ms/lva/mv/m/mvi/2/pl/22/rms/lva,lva/dover/11/pacing/0/keepalive/yes/fexp/51355912,51552689,51565116,51565682,51580968/mt/1759031330/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,rqh,xpc,playlist_duration,manifest_duration,bui,spc,vprv,playlist_type/sig/AJfQdSswRAIgF9jxri0lQZtcWkYQA266Y0EsPP8e_tAoQL8KwTAJ2dcCIEfwfwbD8mIC7oCaea5PKFGh2oW356hU6YXs9uurm3TU/lsparams/hls_chunk_host,initcwndbps,met,mh,mm,mn,ms,mv,mvi,pl,rms/lsig/APaTxxMwRQIgFS8Dk4elsUS9OupouNccC33mW8vA_6KLReom1WBrs_UCIQDsadr1o5TvejURYkRJGiuB8I5gbqQUyrh4bAthHot3-A%3D%3D/playlist/index.m3u8

## 透過ffmpeg將m3u8轉成rtsp後發給mediamtx
ffmpeg -i "https://manifest.googlevideo.com/api/...../playlist/index.m3u8" \
       -c:v copy \
       -an \
       -f rtsp \
       -rtsp_transport tcp \
       rtsp://localhost:8554/stream

範例如下所示:
ffmpeg -i "https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1759053394/ei/8rHYaLzmJvL0pt8PjP2G8Ao/ip/123.192.232.66/id/UCG1aXVO8H8.18/itag/96/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D137/rqh/1/hls_chunk_host/rr2---sn-3cgv-un5ez.googlevideo.com/xpc/EgVo2aDSNQ%3D%3D/playlist_duration/30/manifest_duration/30/bui/ATw7iSVenlYJTHYCuhAsyo9H-xhxZNugBCApC25ErF5UR0AtGRoPwktI7LWaMJG32kN9nhYohI1e06X8/spc/hcYD5ZeSr_Vj8AagNiVwMOy3gcyAYzDC3Ug0EaPk0cGx7PTQ1AUU8ah0j6fmmwWgbRI/vprv/1/playlist_type/DVR/initcwndbps/3726250/met/1759031794,/mh/zD/mm/44/mn/sn-3cgv-un5ez/ms/lva/mv/m/mvi/2/pl/22/rms/lva,lva/dover/11/pacing/0/keepalive/yes/fexp/51355912,51552689,51565116,51565682,51580968/mt/1759031330/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,rqh,xpc,playlist_duration,manifest_duration,bui,spc,vprv,playlist_type/sig/AJfQdSswRAIgF9jxri0lQZtcWkYQA266Y0EsPP8e_tAoQL8KwTAJ2dcCIEfwfwbD8mIC7oCaea5PKFGh2oW356hU6YXs9uurm3TU/lsparams/hls_chunk_host,initcwndbps,met,mh,mm,mn,ms,mv,mvi,pl,rms/lsig/APaTxxMwRQIgFS8Dk4elsUS9OupouNccC33mW8vA_6KLReom1WBrs_UCIQDsadr1o5TvejURYkRJGiuB8I5gbqQUyrh4bAthHot3-A%3D%3D/playlist/index.m3u8" \
       -c:v copy \
       -an \
       -f rtsp \
       -rtsp_transport tcp \
       rtsp://localhost:8554/stream

## 使用ffplay撥放串流, 並且將視窗寬度限制在1280
$ffplay -x 1280 rtsp://localhost:8554/stream


### 將yt-dlp + ffmpeg + mediamtx組合起來放在mediamtx.yaml中
由yt-dlp進行影像解碼後傳入ffmpeg, 由ffmpeg丟給mediamtx轉成rtsp串流

ffmpeg加上-muxdelay會讓破圖情況好一些, 不過延遲會稍微長一點

youtube_cam:
    runOnDemand: >
      sh -c 'yt-dlp -f 96 --fragment-retries 10 --retry-sleep 3 -o - "https://www.youtube.com/watch?v=UCG1aXVO8H8" |
      ffmpeg -re -i pipe:0 -c:v copy -an -muxdelay 0.2
      -f rtsp -rtsp_transport tcp rtsp://localhost:8554/youtube_cam'
    # 子程序（上面這條管線）掛了就重啟
    runOnDemandRestart: yes
    # 等待子程序開始「成功發佈」的最長時間，超過就放棄這次（避免卡死）
    runOnDemandStartTimeout: 15s
    # 當最後一個讀者斷線多久後把子程序關掉（避免一直佔資源）
    runOnDemandCloseAfter: 10s
    #（選用）你也可在這裡加 runOnUnDemand 做收尾腳本



```


## 分析URL問題
```
StreamLink取得的m3u8 URL
https://manifest.googlevideo.com/api/manifest/hls_variant/expire/1759055116/ei/rLjYaPSBL7nk29gP7_C7mQ4/ip/123.192.232.66/id/UCG1aXVO8H8.18/source/yt_live_broadcast/requiressl/yes/xpc/EgVo2aDSNQ%3D%3D/hfr/1/playlist_duration/30/manifest_duration/30/maudio/1/bui/ATw7iSU1n8ITdmoVkqn1_RrWSzAElZnEx74nDY2G8Nt6tQg6KFvCctK5npRvrTCDaf1236P6KaxYfIAg/spc/hcYD5U9QrUvvnG2qlafrGueRynA0L2PCe0KpMV1q_1X6VCqihcsWItRBNrtBFD_aJ-0-EXzZVm0/vprv/1/go/1/rqh/5/pacing/0/nvgoi/1/ncsapi/1/keepalive/yes/fexp/51355912%2C51552689%2C51565115%2C51565682%2C51580968%2C51593650/dover/11/itag/0/playlist_type/DVR/sparams/expire%2Cei%2Cip%2Cid%2Csource%2Crequiressl%2Cxpc%2Chfr%2Cplaylist_duration%2Cmanifest_duration%2Cmaudio%2Cbui%2Cspc%2Cvprv%2Cgo%2Crqh%2Citag%2Cplaylist_type/sig/AJfQdSswRQIhAMrO-YLsFDSXy3N-LtX3GNtJU8rttio1fewYEihmBGWMAiBMSOEBYbTU3ziDZdmym_hPt4swnnIwfUCjf1CsyM9QVw%3D%3D/file/index.m3u8

yt-dlp取得的m3u8 URL
https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1759055161/ei/2bjYaL6fKr-SvcAP7sDpwQk/ip/123.192.232.66/id/UCG1aXVO8H8.18/itag/96/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D137/rqh/1/hls_chunk_host/rr2---sn-3cgv-un5ez.googlevideo.com/xpc/EgVo2aDSNQ%3D%3D/playlist_duration/30/manifest_duration/30/bui/ATw7iSXKcDmbn9GfGbRKXApSrMrO3r4gXVecpv9qMOg0rqppzwoiJ1OJxmShS37A9iw1gMJrJw8LA8W2/spc/hcYD5Y5I0lEOZ3NvoFPYuKOSSVcaembJmNULxALlCuUeD8HiZ0LeNl2eyfq-VQc5HKc/vprv/1/playlist_type/DVR/initcwndbps/3751250/met/1759033561,/mh/zD/mm/44/mn/sn-3cgv-un5ez/ms/lva/mv/m/mvi/2/pl/22/rms/lva,lva/dover/11/pacing/0/keepalive/yes/fexp/51355912,51552689,51565116,51565681,51580968/mt/1759033256/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,rqh,xpc,playlist_duration,manifest_duration,bui,spc,vprv,playlist_type/sig/AJfQdSswRQIhAN1O2kUSFN1pfSXGraKvasR8wDAHoRmA9PGZ8z-PvmhKAiBQiClUGg8BwY181-sQrE0dabokrG6-yu8Q4URSy3nzEA%3D%3D/lsparams/hls_chunk_host,initcwndbps,met,mh,mm,mn,ms,mv,mvi,pl,rms/lsig/APaTxxMwRQIhALhWVsfJ5gsxZETHfFD1GNolVMJOS1Eh7TJNBMwYWG8eAiBeR6RG0CeL656qJcfMD16wdWS1a6-nw8hRW5f2gM0O0w%3D%3D/playlist/index.m3u8
```

## Youtube串流來源
KC Zoo Polar Bear Cam
https://www.youtube.com/watch?v=BSUnBPvX9K4

Trevor-Lovejoy Zoo Red Pandas LIVE
https://www.youtube.com/watch?v=e3EP1XCH0KQ

台東多良車站即時影像 Taitung Duoliang Station Live Camera
https://www.youtube.com/watch?v=UCG1aXVO8H8

Like this LIVE CAM Nevskiy avenue St. Petersburg Russia. Невский пр. Санкт-Петербург, Гостиный двор
https://www.youtube.com/watch?v=h1wly909BYw


Hermosa Beach Good Stuff Strand Cam. Live Camera Stream from Southern California
https://www.youtube.com/watch?v=yJgfAV8lXyI


日本北海道札幌 即時影像 Live | 狸小路八条 | lofi, beats to relax
https://www.youtube.com/watch?v=CF1vS8DdBIk


Jackson Town Square Live PTZ webcam - SeeJH.ai
https://www.youtube.com/watch?v=B_waF26In9o


有線條的影片
【LIVE】大阪 道頓堀 ライブカメラ　osaka Dotonbori LiveCamera
https://www.youtube.com/watch?v=Nbs_WkWTD7M


瑞光港墘
https://tw.live/cam/?id=BOT113

twitch直播
https://www.twitch.tv/zrush

streamlink --stream-url "https://www.twitch.tv/zrush" best


yt-dlp -f 96 -o - "https://www.youtube.com/watch?v=UCG1aXVO8H8" | \
ffmpeg -re -i pipe:0 -c:v copy -an -f rtsp -rtsp_transport tcp rtsp://localhost:8554/youtube_cam


## 參考資料:
Frigate_移動物體與偵測的作法

https://docs.frigate-cn.video/frigate/video_pipeline#%E8%A7%86%E9%A2%91%E6%B5%81%E7%A8%8B%E8%AF%A6%E8%BF%B0

可參考這一段程式:https://github.com/blakeblackshear/frigate/blob/b1a5896b537cad54fe13bf7090b082d0214be44e/frigate/motion/frigate_motion.py#L70-L132

