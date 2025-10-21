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

export { stateBorderClass };
