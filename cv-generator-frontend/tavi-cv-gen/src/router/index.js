import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AboutView from '@/views/AboutView.vue'
import FormView from '@/views/FormView.vue'
import PdfView from '@/views/PdfView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import MyCvsView from '@/views/MyCvsView.vue'

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
    path: '/PDF/:cvId?',
    name: 'pdf',
    component: PdfView,
    props: true
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView
  },
  {
    path: '/my-cvs',
    name: 'my-cvs',
    component: MyCvsView
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
