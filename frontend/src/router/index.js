import { createRouter, createWebHistory } from "vue-router";

import Home from "../views/Home.vue";
import Consult from "../views/Consult.vue";
import Advice from "../views/Advice.vue";
import Wiki from "../views/Wiki.vue";
import Me from "../views/Me.vue";

const routes = [
  { path: "/", redirect: "/home" },
  { path: "/home", component: Home, meta: { tab: "home" } },
  { path: "/consult", component: Consult, meta: { tab: "consult" } },
  { path: "/advice", component: Advice, meta: { tab: "advice" } },
  { path: "/wiki", component: Wiki, meta: { tab: "wiki" } },
  { path: "/me", component: Me, meta: { tab: "me" } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
