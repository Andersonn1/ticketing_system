#!/usr/bin/env bash
set -euo pipefail

force="${1:-}"
if [[ -n "${force}" && "${force}" != "--force" ]]; then
  echo "Usage: $0 [--force]" >&2
  exit 1
fi

shopt -s nullglob dotglob

templates=( *.env.TEMPLATE *.env.TEAMPLATE )
if [[ ${#templates[@]} -eq 0 ]]; then
  echo "No template files found matching *.env.TEMPLATE or *.env.TEAMPLATE"
  exit 0
fi

copied=0
skipped=0

for template in "${templates[@]}"; do
  target=""
  if [[ "${template}" == *.env.TEMPLATE ]]; then
    target="${template%.TEMPLATE}"
  elif [[ "${template}" == *.env.TEAMPLATE ]]; then
    target="${template%.TEAMPLATE}"
  fi

  if [[ -z "${target}" ]]; then
    echo "Skipping unrecognized template file: ${template}"
    ((skipped+=1))
    continue
  fi

  if [[ -e "${target}" && "${force}" != "--force" ]]; then
    echo "Skipping existing file: ${target}"
    ((skipped+=1))
    continue
  fi

  cp "${template}" "${target}"
  echo "Created ${target} from ${template}"
  ((copied+=1))
done

pgpass_file="pgadmin/pgpass"
pgpass_value="postgres:5432:*:postgres:changeme"
mkdir -p "$(dirname "${pgpass_file}")"

if [[ -e "${pgpass_file}" && "${force}" != "--force" ]]; then
  echo "Skipping existing file: ${pgpass_file}"
  ((skipped+=1))
else
  printf '%s\n' "${pgpass_value}" > "${pgpass_file}"
  chmod 600 "${pgpass_file}"
  echo "Created ${pgpass_file}"
  ((copied+=1))
fi

echo "Done. Created ${copied} file(s), skipped ${skipped} file(s)."
