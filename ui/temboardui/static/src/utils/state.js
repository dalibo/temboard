function stateBorderClass(state) {
  const classes = ["border"];
  if (state != "OK" && state != "UNDEF") {
    classes.push("border-" + state.toLowerCase());
  }
  if (state == "CRITICAL") {
    classes.push("border-2");
  }
  return classes;
}

function stateBgClass(state) {
  const classes = [];
  if (state == "UNDEF") {
    classes.push("text-bg-light");
  } else if (state == "OK") {
    classes.push("text-success");
  } else {
    classes.push("text-bg-" + state.toLowerCase());
  }
  return classes;
}

export { stateBgClass, stateBorderClass };
