/* global instances, isAdmin, Vue */
import Vue from 'vue'
import VueRouter from 'vue-router'

import './fscreen.js'
import InstanceList from './components/home/InstanceList.vue'

Vue.use(VueRouter)


window.instancesVue = new Vue({
  el: '#instances',
  data: function() { return {
    currentRole
  } },
  router: new VueRouter(),
  components: {
    "instance-list": InstanceList
  },
  template: `
  <instance-list v-bind:isAdmin="currentRole.isAdmin">
  </instance-list>
  `
});

$('.fullscreen').on('click', function(e) {
  e.preventDefault();
  $(this).addClass('d-none');
  const el = $(this).parents('.container-fluid')[0]
  fscreen.requestFullscreen(el);
});

fscreen.onfullscreenchange = function onFullScreenChange(event) {
  if (!fscreen.fullscreenElement) {
    $('.fullscreen').removeClass('d-none');
  }
}

// hide fullscreen button if not supported
$('.fullscreen').toggleClass('d-none', !fscreen.fullscreenEnabled);
