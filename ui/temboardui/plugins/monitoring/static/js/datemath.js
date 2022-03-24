/* global define, moment, _ */
/*
 * This is a port of the excellent grafana's dateMath utils package.
 * From TypeScript to pure Javascript.
 * See https://github.com/grafana/grafana/blob/master/public/app/core/utils/datemath.ts
 *
 * Parses humanized date strings like: 'now-1d', 'now/d', 'now-7d/d'.
 *
 * Requires `moment` and `loadash`.
 */
(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
      global.dateMath = factory();
}(this, (function () {
  'use strict';

  var units = ['y', 'M', 'w', 'd', 'h', 'm', 's'];
  function parse(text, roundUp, timezone) {
    if (!text) {
      return undefined;
    }
    if (moment.isMoment(text)) {
      return text;
    }
    if (_.isDate(text)) {
      return moment(text);
    }
    var time;
    var mathString = '';
    var index;
    var parseString;
    if (text.substring(0, 3) === 'now') {
      if (timezone === 'utc') {
        time = moment.utc();
      } else {
        time = moment();
      }
      mathString = text.substring('now'.length);
    } else {
      index = text.indexOf('||');
      if (index === -1) {
        parseString = text;
        mathString = ''; // nothing else
      } else {
        parseString = text.substring(0, index);
        mathString = text.substring(index + 2);
      }
      // We're going to just require ISO8601 timestamps, k?
      time = moment(parseString, moment.ISO_8601);
    }
    if (!mathString.length) {
      return time;
    }
    return parseDateMath(mathString, time, roundUp);
  }
  function isValid(text) {
    var date = parse(text);
    if (!date) {
      return false;
    }
    if (moment.isMoment(date)) {
      return date.isValid();
    }
    return false;
  }
  function parseDateMath(mathString, time, roundUp) {
    var dateTime = time;
    var i = 0;
    var len = mathString.length;
    while (i < len) {
      var c = mathString.charAt(i++);
      var type;
      var num;
      var unit;
      if (c === '/') {
        type = 0;
      } else if (c === '+') {
        type = 1;
      } else if (c === '-') {
        type = 2;
      } else {
        return undefined;
      }
      if (isNaN(mathString.charAt(i))) {
        num = 1;
      } else if (mathString.length === 2) {
        num = mathString.charAt(i);
      } else {
        var numFrom = i;
        while (!isNaN(mathString.charAt(i))) {
          i++;
          if (i > 10) {
            return undefined;
          }
        }
        num = parseInt(mathString.substring(numFrom, i), 10);
      }
      if (type === 0) {
        // rounding is only allowed on whole, single, units (eg M or 1M, not 0.5M or 2M)
        if (num !== 1) {
          return undefined;
        }
      }
      unit = mathString.charAt(i++);
      if (!_.includes(units, unit)) {
        return undefined;
      } else {
        if (type === 0) {
          if (roundUp) {
            dateTime.endOf(unit);
          } else {
            dateTime.startOf(unit);
          }
        } else if (type === 1) {
          dateTime.add(num, unit);
        } else if (type === 2) {
          dateTime.subtract(num, unit);
        }
      }
    }
    return dateTime;
  }

  return {
    parse: parse,
    isValid: isValid
  };

})));
