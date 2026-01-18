#!/usr/bin/env bash
set -e
install_dir="${1:?install directory required}"
if ! [ -d "$install_dir" ]; then
	echo "Error: $install_dir is not a directory"
	exit 1
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
git_root="$(git rev-parse --show-toplevel)"

find-file-in-parents() {
	local target_file="$1" cwd="$2" stop="$(cd "$(dirname "$git_root")" && pwd)" path
	while [[ $cwd != $stop ]]; do
		path="$cwd/$target_file"
		[[ -f $path ]] && { echo "$path"; return 0 ; }
		cwd="${cwd%/*}"
	done
	return 1
}

toml_path="$(find-file-in-parents pyproject.toml "$script_dir")"
toml_dir="$(dirname "$toml_path")"

read exec_name entrypoint < <(python <<-EOF
	import tomllib
	t=tomllib.load(open('$toml_path','rb'))
	print(next(f"{k}\t{v}" for k,v in t['project']['scripts'].items()))
	EOF
)

output_path="$install_dir/$exec_name"
work_dir="$(mktemp --directory)"
trap "rm -r $work_dir" EXIT
pip install "$toml_dir" --no-cache-dir --target="$work_dir"
python -m zipapp \
	--output "$output_path" \
	--python="$(which python)" \
	--main "$entrypoint" \
	"$work_dir"

[[ -x "$output_path" ]] && "$output_path" --version