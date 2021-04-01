%global srcname gptsum

Name:           python-%{srcname}
Version:        %{_version}
Release:        1%{?dist}
Summary:        A tool to make disk images using GPT partitions self-verifiable

License:        APL 2.0
URL:            https://github.com/NicolasT/gptsum
Source0:        %{pypi_source}

BuildArch:      noarch

%global _description %{expand:
A tool to make disk images using GPT partitions self-verifiable, like isomd5sum.}

%description %_description

%package -n python%{python3_pkgversion}-%{srcname}
Summary:        %{summary}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools

# Dependencies
%if 0%{python3_version_nodots} < 37
BuildRequires:  %{py3_dist dataclasses}
%endif
%if 0%{python3_version_nodots} < 38
BuildRequires:  %{py3_dist importlib-metadata}
%endif

# Test dependencies
BuildRequires:  util-linux
BuildRequires:  %{py3_dist packaging}
BuildRequires:  %{py3_dist py}
BuildRequires:  %{py3_dist pytest}
BuildRequires:  %{py3_dist pytest-benchmark}
BuildRequires:  %{py3_dist pytest-mock}

%description -n python%{python3_pkgversion}-%{srcname} %_description

%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

%check
%pytest

%files -n python%{python3_pkgversion}-%{srcname}
%license LICENSE
%doc README.rst
%{_bindir}/gptsum
%{python3_sitelib}/%{srcname}/
%{python3_sitelib}/%{srcname}-%{version}-py%{python3_version}.egg-info/

%changelog
* Wed Mar 31 2021 Nicolas Trangez <ikke@nicolast.be> 0.0.9
- New package.
