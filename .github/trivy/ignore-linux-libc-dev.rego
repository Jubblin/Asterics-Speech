# Containers use the host kernel; linux-libc-dev header CVEs are not runtime risks.
package trivy

default ignore = false

ignore {
  input.PkgName == "linux-libc-dev"
}
