import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AboutView from '@/views/AboutView.vue'
import FormView from '@/views/FormView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/about',
    name: 'about',
    component: AboutView
  },
  {
    path: '/form',
    name: 'form',
    component: FormView
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
