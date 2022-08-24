moment.fn.preciseDiff = function(d2, precision) {
  return moment.preciseDiff(this, d2, precision);
};
moment.preciseDiff = function(d1, d2, precision) {

  var STRINGS = {
    nodiff: '0',
    year: 'year',
    years: 'years',
    month: 'month',
    months: 'months',
    day: 'day',
    days: 'days',
    hour: 'hour',
    hours: 'hours',
    minute: 'min',
    minutes: 'min',
    second: 's',
    seconds: 's',
    millisecond: 'ms',
    milliseconds: 'ms',
    microsecond: 'µs',
    microseconds: 'µs',
    delimiter: ' '
  };

  var m1 = moment(d1), m2 = moment(d2);
  if (m1.isAfter(m2) || (m1.isSame(m2) && m1._i > m2._i)) {
    var tmp = m1;
    m1 = m2;
    m2 = tmp;
  }
  var yDiff = m2.year() - m1.year();
  var mDiff = m2.month() - m1.month();
  var dDiff = m2.date() - m1.date();
  var hourDiff = m2.hour() - m1.hour();
  var minDiff = m2.minute() - m1.minute();
  var secDiff = m2.second() - m1.second();
  var msecDiff = m2.millisecond() - m1.millisecond();
  var microsecDiff = 0;
  if(typeof m1._i == "number" && typeof m2._i == "number"){
    microsecDiff = Math.round((1000 * (m2._i - Math.floor(m2)) - 1000 * (m1._i - Math.floor(m1))))
    } else {
      if (m1.isSame(m2)) {
        return STRINGS.nodiff;
      }
    }
    if(microsecDiff < 0){
      microsecDiff = 1000 + microsecDiff;
      msecDiff--;
    }
    if(msecDiff < 0) {
      msecDiff = 1000 + secDiff;
      secDiff--;
    }
    if (secDiff < 0) {
      secDiff = 60 + secDiff;
      minDiff--;
    }
    if (minDiff < 0) {
      minDiff = 60 + minDiff;
      hourDiff--;
    }
    if (hourDiff < 0) {
      hourDiff = 24 + hourDiff;
      dDiff--;
    }
    if (dDiff < 0) {
      var daysInLastFullMonth = moment(m2.year() + '-' + (m2.month() + 1), "YYYY-MM").subtract('months', 1).daysInMonth();
      if (daysInLastFullMonth < m1.date()) { // 31/01 -> 2/03
      dDiff = daysInLastFullMonth + dDiff + (m1.date() - daysInLastFullMonth);
    } else {
      dDiff = daysInLastFullMonth + dDiff;
    }
    mDiff--;
  }
  if (mDiff < 0) {
    mDiff = 12 + mDiff;
    yDiff--;
  }
  function pluralize(num, word) {
    return num + ' ' + STRINGS[word + (num === 1 ? '' : 's')];
  }
  var result = [];
  if (yDiff) {
    result.push(pluralize(yDiff, 'year'));
  }
  if (mDiff) {
    result.push(pluralize(mDiff, 'month'));
  }
  if (dDiff) {
    result.push(pluralize(dDiff, 'day'));
  }
  if (hourDiff) {
    result.push(pluralize(hourDiff, 'hour'));
  }
  if (minDiff) {
    result.push(pluralize(minDiff, 'minute'));
  }
  if (secDiff) {
    result.push(pluralize(secDiff, 'second'));
  }
  if (msecDiff) {
    result.push(pluralize(msecDiff, 'millisecond'));
  }
  if(microsecDiff){
    result.push(pluralize(microsecDiff, 'microsecond'));
  }
  if(result.length == 0){
    return "0";
  }
  // Keep only the first 'precision' results, more it too precise
  if (precision) {
    result = result.slice(0, precision);
  }
  return result.join(STRINGS.delimiter);
};
