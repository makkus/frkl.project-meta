#!/usr/bin/env bash

DEFAULT_PYTHON_VERSION="3.9.1"
DEFAULT_PYINSTALLER_VERSION="4.2"

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function command_exists {
   type "$1" > /dev/null 2>&1 ;
}

# mac sometimes does not have 'realpath' available
if ! command_exists realpath; then

  function realpath() {

      local _X="$PWD"
      local _LNK=$1
      cd "$(dirname "$_LNK")"
      if [ -h "$_LNK" ]; then
          _LNK="$(readlink "$_LNK")"
          cd "$(dirname "$_LNK")"
      fi
      local _basename=$(basename "$_LNK")

      if [[ "${_basename}" = "/" ]]; then
          _basename=""
      fi
      if [[ "${PWD}" = "/" ]]; then
          echo "/${_basename}"
      else
          echo "$PWD/${_basename}"
      fi

      cd "$_X"

  }

fi


function ensure_python () {

    local python_version="${1}"

    export PATH="${HOME}/.pyenv/bin:$PATH"

    # pyenv
    if ! command_exists pyenv; then

        if command_exists curl; then
            curl https://pyenv.run | bash
        elif command_exists wget; then
            wget -O- https://pyenv.run | bash
        else
            echo "Can't install pyenv. Need wget or curl."
            exit 1
        fi
    fi

    local python_path="${HOME}/.pyenv/versions/${python_version}"
    if [ -n "${python_version}" ]; then
      # python version
      if [ ! -e "${python_path}" ]; then
          pyenv update
          env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install "${python_version}"
          if [ $? -ne 0 ]; then
            echo "Can't install requested Python version: ${python_version}"
#            exit 1
          fi
          eval "$(pyenv init -)"
          eval "$(pyenv virtualenv-init -)"

      fi
    else
      echo "No Python version provided"
      exit 1
    fi
}

function get_python_path () {

    local python_version="${1}"

    local python_path="${HOME}/.pyenv/versions/${python_version}/bin/python"
    echo ${python_path}

}


function ensure_virtualenv () {

   local python_path="${1}"
   local python_version="${2}"
   local venv_name="${3}"

    local virtualenv_path="${HOME}/.cache/frkl-build-envs/${venv_name}-${python_version}"
    if [ ! -e "${virtualenv_path}/bin/activate" ]; then
      cmd=( "${python_path}" "-m" "venv" "${virtualenv_path}" )
      "${cmd[@]}"
    fi

    echo ${virtualenv_path}
}


function install_requirements () {

    local venv_path="${1}"
    local pyinstaller_version="${2}"
    local requirements_file="${3}"

    pip install -U pip
    pip install -U setuptools
    pip install "pyinstaller==${pyinstaller_version}"

    if [ -n "${requirements_file}" ]; then
        echo "installing dependencies from: ${requirements_file}"
        pip install -U --extra-index-url https://pkgs.frkl.io/frkl/dev --extra-index-url https://pkgs.frkl.dev/pypi -r "${requirements_file}"
    fi

    pip install git+https://gitlab.com/frkl/frkl.project_meta.git

    pip install -U --upgrade-strategy eager --extra-index-url https://pkgs.frkl.io/frkl/dev --extra-index-url https://pkgs.frkl.dev/pypi "${project_root}[all, build]"

    echo " --> dependencies installed"

}


function build_artifact () {

    local project_root="${1}"
    local build_dir="${2}"
    local venv_name="${3}"
    local python_version="${4}"
    local pyinstaller_version="${5}"
    local requirements_file="${6}"
    local output_dir="${7}"
    local spec_file="${8}"

    local target="${output_dir}/${OSTYPE}"

    mkdir -p "${build_dir}"

    echo "making sure Python version is available..."
    ensure_python "${python_version}"
    python_path=$(get_python_path "${python_version}")
    echo " -> Python ${python_version} exists"
    echo

    echo "making sure virtualenv ${venv_name} exists..."
    venv_path=$(ensure_virtualenv ${python_path} ${python_version} ${venv_name})
    echo " -> virtualenv exits: ${venv_path}"
    echo

    source "${venv_path}/bin/activate"

    echo "preparing build"
    install_requirements "${venv_path}" "${pyinstaller_version}" "${requirements_file}"

    mkdir -p "${output_dir}"

    echo "building package"
    echo $venv_path

    local temp_dir="${build_dir}/build-${RANDOM}"

    mkdir -p "${temp_dir}"

    cd "${project_root}"

    make project-info
    make binary-config

    pyinstaller --clean -y --dist "${target}" --workpath "${temp_dir}" "${spec_file}"

    rm -rf "${temp_dir}"

    deactivate

    echo "  -> package built"

}


function main () {

    local project_root="${1}"
    local build_dir="${2}"
    local venv_name="${3}"
    local python_version="${4}"
    local pyinstaller_version="${5}"
    local requirements_file="${6}"
    local output_dir="${7}"
    local spec_file="${8}"

    # activate pyenv if already installed
#    if [ -f "$HOME/.pyenv/.pyenvrc" ]; then
#      source "$HOME/.pyenv/.pyenvrc"
#    fi

    if [ -z "${DOCKER_BUILD}" ]; then
        DOCKER_BUILD=false
    fi

    if [ -f /.dockerenv ] || [ "$DOCKER_BUILD" != true ]; then

           build_artifact "${project_root}" "${build_dir}" "${venv_name}" "${python_version}" "${pyinstaller_version}" "${requirements_file}" "${output_dir}" "${spec_file}"

    else
            # TODO: fix this
            echo "Docker build currently not supported."
            exit 1
#            docker run -v "${THIS_DIR}/..:/src/" registry.gitlab.com/freckles-io/freckles-build "${entrypoint}"

    fi
}

while [[ -n "$1" ]]; do
  case "$1" in
  --project-root)
    shift
    PROJECT_ROOT="${1}"
    ;;
  --build-dir)
    shift
    BUILD_DIR="${1}"
    ;;
  --python-version)
    shift
    PYTHON_VERSION="${1}"
    ;;
  --pyinstaller-version)
    shift
    PYINSTALLER_VERSION="${1}"
    ;;
  --requirements)
    shift
    REQUIREMENTS_FILE="${1}"
    ;;
  --output-dir)
    shift
    OUTPUT_DIR="${1}"
    ;;
  --spec-file)
    shift
    SPEC_FILE="${1}"
    ;;
  --venv-name)
    shift
    VENV_NAME="${1}"
    ;;
  --)
    shift
    break
    ;;
  -*|--*=) # unsupported flags
    echo "Error: Invalid argument '${1}'" >&2
    exit 1
    ;;
  esac
  shift
done

echo

if [ -z "${PROJECT_ROOT}" ]
then
   PROJECT_ROOT=$(pwd)
fi
if [ ! -d "${PROJECT_ROOT}" ]
then
  echo "project root '${PROJECT_ROOT} does not exist or is not directory"
  exit 1
fi
PROJECT_ROOT=$(realpath "${PROJECT_ROOT}")

if [ -z "${BUILD_DIR}" ]
then
  BUILD_DIR="/tmp"
fi
mkdir -p ${BUILD_DIR}
if [ ! -d "${BUILD_DIR}" ]
then
  echo "can't create build dir '${BUILD_DIR}"
  exit 1
fi
BUILD_DIR=$(realpath "${BUILD_DIR}")

if [ -z "${VENV_NAME}" ]
then
  VENV_NAME=$(basename "${PROJECT_ROOT}-build")
fi

if [ -z "${PYTHON_VERSION}" ]
then
  PYTHON_VERSION="${DEFAULT_PYTHON_VERSION}"
fi

if [ -z "${PYINSTALLER_VERSION}" ]
then
  PYINSTALLER_VERSION="${DEFAULT_PYINSTALLER_VERSION}"
fi

if [ -z "${REQUIREMENTS_FILE}" ]
then
  REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements-build.txt"
fi
if [ -f "${REQUIREMENTS_FILE}" ]
then
  REQUIREMENTS_FILE=$(realpath "${REQUIREMENTS_FILE}")
else
  unset REQUIREMENTS_FILE
fi

if [ -z "${OUTPUT_DIR}" ]
then
  OUTPUT_DIR="${PROJECT_ROOT}/dist"
fi
mkdir -p ${OUTPUT_DIR}
if [ ! -d "${OUTPUT_DIR}" ]
then
  echo "can't create output dir '${OUTPUT_DIR}"
  exit 1
fi
OUTPUT_DIR=$(realpath "${OUTPUT_DIR}")

if [ -z ${SPEC_FILE} ]
then
  SPEC_FILE="${THIS_DIR}/onefile.spec"
fi
if [ ! -f "${SPEC_FILE}" ]
then
  echo "spec file '${SPEC_FILE} does not exist"
  exit 1
fi
SPEC_FILE=$(realpath "$SPEC_FILE")

echo "project root: ${PROJECT_ROOT}"
echo "requirements file: ${REQUIREMENTS_FILE}"
echo "spec file: ${SPEC_FILE}"
echo "output dir: ${OUTPUT_DIR}"
echo "build dir: ${BUILD_DIR}"
echo "venv name: ${VENV_NAME}"
echo "python version: ${PYTHON_VERSION}"
echo "pyinstaller version: ${PYINSTALLER_VERSION}"

echo
echo "starting build..."
echo

set -e
#set -x

main "${PROJECT_ROOT}" "${BUILD_DIR}" "${VENV_NAME}" "${PYTHON_VERSION}" "${PYINSTALLER_VERSION}" "${REQUIREMENTS_FILE}" "${OUTPUT_DIR}" "${SPEC_FILE}"

set +e
#set +x

echo
echo "build finished"
echo
