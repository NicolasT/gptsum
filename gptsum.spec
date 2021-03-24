%global pypi_name gptsum

Name:           python-%{pypi_name}
Version:        0.0.6
Release:        1%{?dist}
Summary:        A tool to make disk images using GPT partitions self-verifiable

License:        ASL 2.0
URL:            https://github.com/NicolasT/gptsum
Source0:        %{pypi_source}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)

%description
 A tool to make disk images using GPT_ partitions self-verifiable, like
isomd5sum. Note this *only* works for read-only, immutable images!

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       (python3dist(dataclasses) >= 0.6 with python3dist(dataclasses) < 0.9)
Requires:       (python3dist(importlib-metadata) >= 3.7.3 with python3dist(importlib-metadata) < 4)
Requires:       python3dist(setuptools)
%description -n python3-%{pypi_name}
 A tool to make disk images using GPT_ partitions self-verifiable, like
isomd5sum. Note this *only* works for read-only, immutable images!

%prep
%autosetup -n %{pypi_name}-%{version}

%build
%py3_build

%install
%py3_install

%files -n python3-%{pypi_name}
%license LICENSE
%doc README.rst
%{_bindir}/gptsum
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py%{python3_version}.egg-info

%changelog
* Wed Mar 24 2021 Nicolas Trangez <ikke@nicolast.be> - 0.0.6-1
- Initial package.
