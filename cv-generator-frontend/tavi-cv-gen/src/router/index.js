import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AboutView from '@/views/AboutView.vue'
import FormView from '@/views/FormView.vue'
import PdfView from '@/views/PdfView.vue'

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
  },
  {
    path: '/PDF',
    name: 'pdf',
    component: PdfView
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
