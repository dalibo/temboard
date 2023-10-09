import _ from "lodash";
const durationSecond = 1000;
const durationMinute = durationSecond * 60;
const durationHour = durationMinute * 60;
const durationDay = durationHour * 24;

function formatDuration(ms, rounded) {
  let results = [];
  const µs = Math.round((ms - Math.floor(ms)) * 1000);
  ms = Math.floor(ms);
  const d = Math.trunc(ms / durationDay);
  results.push(d + " d");
  ms = ms - d * durationDay;
  const h = Math.trunc(ms / durationHour);
  results.push(h + " h");
  ms = ms - h * durationHour;
  const m = Math.trunc(ms / durationMinute);
  results.push(m + " min");
  ms = ms - m * durationMinute;
  const s = Math.trunc(ms / durationSecond);
  results.push(s + " s");
  ms = ms - s * durationSecond;
  results.push(ms + " ms");
  results.push(µs + " µs");

  results = _.dropWhile(results, (o) => parseInt(o) == 0);

  if (rounded) {
    // Only keep the first or two firsts values
    const n = parseInt(results[0]) < 3 && parseInt(results[1]) !== 0 ? 2 : 1;
    results = results.slice(0, n);
  }
  return results.length ? results.join(" ") : "0 ms";
}

export { formatDuration };
