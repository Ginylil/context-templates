#!/usr/bin/env bash
set -e
set -o pipefail

log_err(){
  local msg="$1"
  local exit_code="${2:-1}"
  echo -e "[ERROR] $(date) :: $msg"
  exit "$exit_code"
}

log_info(){
  local msg="$1"
  echo -e "[INFO] $(date) :: $msg"
}

main(){
      local input_file_name=$1
      local output_file_name=$2
      local var_name
      local var_value
      local keypair
      if [[ ! -f "$input_file_name" ]] ; then
        log_error "File does not exist - '${input_file_name}'" 44
      else
        cp "$input_file_name" "$output_file_name"
      fi
      while read -r row; do
        if [[ -n "$row" ]]; then
            var_name=$(echo "$row" | cut -f1 -d= 2>/dev/null || true)
            [[ -n "${var_name}" ]] && var_value="$(printenv ${var_name} 2>/dev/null || true)"
            keypair="${var_name}=${var_value}"
            if [[ -n "$var_value" && "$var_value" != "\$$var_name" ]]; then
              log_info "Setting ${var_name} ..."
              sed -i'.bak' -e s~^${var_name}=.*~${keypair}~ "$output_file_name"
            else
              log_info "Skipping empty var - ${var_name}"
            fi
        fi
      done < "${input_file_name}"
}

main "$1" "$2"
