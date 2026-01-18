import { createRouter, createWebHistory } from "vue-router";

import Home from "../views/Home.vue";
import Consult from "../views/Consult.vue";
import Advice from "../views/Advice.vue";
import Wiki from "../views/Wiki.vue";
import Me from "../views/Me.vue";
import AdviceDetail from "../views/AdviceDetail.vue";
import TaskDetail from "../views/TaskDetail.vue";
import WikiDetail from "../views/WikiDetail.vue";

const routes = [
  { path: "/", redirect: "/home" },
  { path: "/home", component: Home, meta: { tab: "home" } },

  { path: "/consult", component: Consult, meta: { tab: "consult" } },

  { path: "/advice", component: Advice, meta: { tab: "advice" } },
  { path: "/advice/:id", component: AdviceDetail, meta: { tab: "advice" } },
  { path: "/task/:id", component: TaskDetail, meta: { tab: "advice" } },

  { path: "/wiki", component: Wiki, meta: { tab: "wiki" } },

  { path: "/me", component: Me, meta: { tab: "me" } },

  { path: "/wiki/:id", component: WikiDetail, meta: { tab: "wiki" } },
  {
    path: "/home",
    component: Home, // 👈 确保这个组件导入是对的
    name: "home"     // 👈 建议加上 name 属性
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
