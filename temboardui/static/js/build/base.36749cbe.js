(window.webpackJsonp=window.webpackJsonp||[]).push([["base"],{"./temboardui/static/js/base.js":function(e,o,s){"use strict";s.r(o),function(e){s("./node_modules/bootstrap/dist/js/bootstrap.js");var o=s("./node_modules/jquery/dist/jquery.js-exposed"),t=s.n(o);t.a,window.$=t.a,t()(function(){var e=window.location,o=t()("ul.nav a").filter(function(){return this.href==e||0==e.href.indexOf(this.href)}).addClass("active").parent().parent().addClass("in").parent();o.is("li")&&o.addClass("active"),t()("#menu-collapse").click(function(e){t()(document.body).toggleClass("sidebar-collapsed"),localStorage.setItem("sidebarCollapsed",t()(document.body).hasClass("sidebar-collapsed")),e.preventDefault(),window.dispatchEvent(new Event("resize"))}),t()(document).ready(function(){t()(function(){t()('[data-toggle="popover"]').popover()}),t()(function(){t()('[data-toggle="tooltip"]').tooltip()})})})}.call(this,s("./node_modules/jquery/dist/jquery.js-exposed"))}},[["./temboardui/static/js/base.js","runtime","vendor","vendors~base"]]]);