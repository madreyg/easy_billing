import { check } from "k6";
import http from "k6/http";

export let options = {
  vus: 300,
  duration: "30s"
};
//нагрузочный тест на операцию "переводе между своими счетами"
export default function() {
  let formdata = { from: "1", to: "2", amount: "3" };
  let headers = { "Content-Type": "application/x-www-form-urlencoded" };
  let params = {
      cookies: { session: ".eJwlzskJAkEQAMBc-u2jj5ltZ5ORPlHwtYsvMXcFAyioN9z6qPMOe9vzrAvcHgk78FQu7K5AF-RrZW0a2ipzTEoKc_fl23LkjGktnVw_EjKsYwu1uSwXanMFs10lRSh1qnEiCa9CKRqpi4gJMcrMh0eNZk24wOus458h-HwBOG4wcA.Xhuniw.3lkuwnXoh-5eLhgCvFwK0GenSh4" }
  }
  let res = http.post("http://127.0.0.1:8080/api/user/1/transaction", formdata, params);

  check(res, {
      "is status 200": (r) => r.status === 201
  });
};
