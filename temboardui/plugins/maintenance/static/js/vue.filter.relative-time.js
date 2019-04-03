/* global Vue, moment */
Vue.filter('relative_time', function (value, allowNegative) {
  allowNegative = allowNegative === false ? false : true;
  if (!value || !allowNegative && moment(value).diff(moment()) < 0) {
    return 'now';
  }
  return moment(value).fromNow();
});
