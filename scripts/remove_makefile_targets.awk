BEGIN {
  while ((getline t < "makefile_targets_to_remove.txt") > 0) {
    targets[t] = 1
  }
  close("makefile_targets_to_remove.txt")
}
function is_target_line(line) {
  for (t in targets) {
    if (line ~ "^" t ":") return t
  }
  return ""
}
{
  # Remove .PHONY lines for these targets
  if ($1 == ".PHONY:") {
    keep = ""
    for (i = 2; i <= NF; i++) {
      if (!( $i in targets )) {
        keep = keep ? keep " " $i : $i
      }
    }
    if (keep) print ".PHONY:" keep
    next
  }
  # Remove recipe blocks for these targets
  if (in_block) {
    if ($0 ~ /^[^ \t].*:/ || $0 ~ /^$/) {
      in_block = 0
    } else {
      next
    }
  }
  tgt = is_target_line($0)
  if (tgt) {
    in_block = 1
    next
  }
  print
} 