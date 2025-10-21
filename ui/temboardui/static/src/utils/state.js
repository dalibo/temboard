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

function stateIcon(state) {
  if (state == "WARNING") {
    return "fa-warning";
  }
  if (state == "CRITICAL") {
    return "fa-burst";
  }
  if (state == "OK") {
    return "fa-check";
  }
  return "";
}

export { stateBgClass, stateBorderClass, stateIcon };
