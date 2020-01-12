


Тестируется на операции перевод между счетами.

          /\      |‾‾|  /‾‾/  /‾/
     /\  /  \     |  |_/  /  / /
    /  \/    \    |      |  /  ‾‾\
   /          \   |  |‾\  \ | (_) |
  / __________ \  |__|  \__\ \___/ .io

  execution: local
     output: -
     script: script.js

    duration: 30s, iterations: -
         vus: 40,  max: 40

    done [==========================================================] 30s / 30s

    ✓ is status 200

    checks.....................: 100.00% ✓ 1422 ✗ 0
    data_received..............: 1.4 MB  46 kB/s
    data_sent..................: 1.3 MB  42 kB/s
    http_req_blocked...........: avg=21.4µs   min=2µs     med=4µs      max=3.14ms   p(90)=7µs      p(95)=12.84µs
    http_req_connecting........: avg=12.04µs  min=0s      med=0s       max=2.99ms   p(90)=0s       p(95)=0s
    http_req_duration..........: avg=414.65ms min=13.56ms med=413.79ms max=781.5ms  p(90)=587.24ms p(95)=625.89ms
    http_req_receiving.........: avg=103.03µs min=45µs    med=97µs     max=971µs    p(90)=138µs    p(95)=156.84µs
    http_req_sending...........: avg=27.67µs  min=11µs    med=22µs     max=1.14ms   p(90)=34µs     p(95)=42µs
    http_req_tls_handshaking...: avg=0s       min=0s      med=0s       max=0s       p(90)=0s       p(95)=0s
    http_req_waiting...........: avg=414.52ms min=12.39ms med=413.66ms max=781.39ms p(90)=587.09ms p(95)=625.78ms
    http_reqs..................: 2864    95.465936/s
    iteration_duration.........: avg=830.57ms min=87.59ms med=844.15ms max=1.06s    p(90)=962.26ms p(95)=994.65ms
    iterations.................: 1422    47.399637/s
    vus........................: 40      min=40 max=40
    vus_max....................: 40      min=40 max=40



          /\      |‾‾|  /‾‾/  /‾/
     /\  /  \     |  |_/  /  / /
    /  \/    \    |      |  /  ‾‾\
   /          \   |  |‾\  \ | (_) |
  / __________ \  |__|  \__\ \___/ .io

  execution: local
     output: -
     script: script.js

    duration: 30s, iterations: -
         vus: 100, max: 100

    done [==========================================================] 30s / 30s

    ✓ is status 200

    checks.....................: 100.00% ✓ 1466  ✗ 0
    data_received..............: 1.4 MB  47 kB/s
    data_sent..................: 1.3 MB  44 kB/s
    http_req_blocked...........: avg=90.16µs  min=1µs      med=4µs      max=7.64ms p(90)=9µs   p(95)=18µs
    http_req_connecting........: avg=75.3µs   min=0s       med=0s       max=7.51ms p(90)=0s    p(95)=0s
    http_req_duration..........: avg=988.46ms min=23.16ms  med=989.25ms max=1.75s  p(90)=1.44s p(95)=1.54s
    http_req_receiving.........: avg=102.07µs min=46µs     med=98µs     max=670µs  p(90)=140µs p(95)=155µs
    http_req_sending...........: avg=37.47µs  min=12µs     med=23µs     max=4.73ms p(90)=36µs  p(95)=48µs
    http_req_tls_handshaking...: avg=0s       min=0s       med=0s       max=0s     p(90)=0s    p(95)=0s
    http_req_waiting...........: avg=988.32ms min=22.3ms   med=989.15ms max=1.75s  p(90)=1.44s p(95)=1.54s
    http_reqs..................: 2979    99.299379/s
    iteration_duration.........: avg=1.98s    min=105.22ms med=2s       max=2.37s  p(90)=2.25s p(95)=2.28s
    iterations.................: 1466    48.866361/s
    vus........................: 100     min=100 max=100
    vus_max....................: 100     min=100 max=100



          /\      |‾‾|  /‾‾/  /‾/
     /\  /  \     |  |_/  /  / /
    /  \/    \    |      |  /  ‾‾\
   /          \   |  |‾\  \ | (_) |
  / __________ \  |__|  \__\ \___/ .io

  execution: local
     output: -
     script: script.js

    duration: 30s, iterations: -
         vus: 300, max: 300

WARN[0007] Request Failed                                error="Post http://127.0.0.1:8080/api/user/1/transaction: dial tcp 127.0.0.1:8080: connect: connection reset by peer"
WARN[0007] Request Failed                                error="Post http://127.0.0.1:8080/api/user/1/transaction: dial tcp 127.0.0.1:8080: connect: connection reset by peer"
WARN[0007] Request Failed                                error="Post http://127.0.0.1:8080/api/user/1/transaction: dial tcp 127.0.0.1:8080: connect: connection reset by peer"
WARN[0007] Request Failed                                error="Post http://127.0.0.1:8080/api/user/1/transaction: dial tcp 127.0.0.1:8080: connect: connection reset by peer"
    done [==========================================================] 30s / 30s

    ✗ is status 200
     ↳  99% — ✓ 916 / ✗ 4

    checks.....................: 99.56% ✓ 916   ✗ 4
    data_received..............: 889 kB 30 kB/s
    data_sent..................: 821 kB 27 kB/s
    http_req_blocked...........: avg=3.32ms   min=0s      med=4µs   max=109.58ms p(90)=20µs  p(95)=28.93ms
    http_req_connecting........: avg=3.29ms   min=0s      med=0s    max=109.5ms  p(90)=0s    p(95)=28.79ms
    http_req_duration..........: avg=1.97s    min=0s      med=1.29s max=28.26s   p(90)=2.21s p(95)=11.8s
    http_req_receiving.........: avg=111µs    min=0s      med=103µs max=1.06ms   p(90)=155µs p(95)=177µs
    http_req_sending...........: avg=107.32µs min=0s      med=23µs  max=3.12ms   p(90)=51µs  p(95)=661.5µs
    http_req_tls_handshaking...: avg=0s       min=0s      med=0s    max=0s       p(90)=0s    p(95)=0s
    http_req_waiting...........: avg=1.97s    min=0s      med=1.29s max=28.26s   p(90)=2.21s p(95)=11.8s
    http_reqs..................: 1971   65.699851/s
    iteration_duration.........: avg=3.26s    min=17.89ms med=2.58s max=29.85s   p(90)=3.11s p(95)=12.7s
    iterations.................: 920    30.666597/s
    vus........................: 300    min=300 max=300
    vus_max....................: 300    min=300 max=300
