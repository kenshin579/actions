# 공통 Release Workflow 구현 체크리스트

## Phase 1: 공통 Workflow 생성 (actions repo)

### 1.1 release.yml 생성
- [x] `actions/.github/workflows/release.yml` 파일 생성
- [x] workflow_call 트리거 설정
- [x] inputs 정의: version_type, tag_prefix, create_release
- [x] outputs 정의: new_version, previous_version, has_changes
- [x] 마지막 태그 조회 로직 구현
- [x] 변경사항 확인 로직 구현
- [x] 새 버전 계산 로직 구현 (major/minor/patch)
- [x] 태그 생성 및 푸시 구현
- [x] GitHub Release 생성 구현 (softprops/action-gh-release)
- [ ] actions repo에서 테스트 실행

### 1.2 docker-publish.yml 생성
- [x] `actions/.github/workflows/docker-publish.yml` 파일 생성
- [x] workflow_call 트리거 설정
- [x] inputs 정의: image_name, platforms, registry
- [x] secrets 정의: DOCKER_USERNAME, DOCKER_PASSWORD
- [x] docker/metadata-action으로 태그 추출
- [x] docker/setup-qemu-action 추가 (multi-platform 지원)
- [x] docker/setup-buildx-action 추가
- [x] docker/login-action으로 registry 로그인
- [x] docker/build-push-action으로 빌드 및 푸시
- [x] GHA 캐시 설정

### 1.3 pypi-publish.yml 생성
- [x] `actions/.github/workflows/pypi-publish.yml` 파일 생성
- [x] workflow_call 트리거 설정
- [x] inputs 정의: python_version, run_tests, test_command, create_release
- [x] secrets 정의: PYPI_API_TOKEN
- [x] test job 구현 (조건부 실행)
- [x] build-and-publish job 구현
- [x] setuptools-scm 버전 관리 설정
- [x] twine upload 구현
- [x] GitHub Release 생성 (dist 파일 첨부)

---

## Phase 2: Repository 마이그레이션

### 2.1 stock-data-batch
- [ ] 기존 `release.yml`을 공통 workflow 호출로 변경
- [ ] 기존 `docker-publish.yml`을 공통 workflow 호출로 변경
- [ ] 테스트: workflow_dispatch로 release 실행
- [ ] 테스트: tag push 시 docker 이미지 빌드 확인

### 2.2 korea-investment-stock
- [ ] `release.yml` 추가 (공통 workflow 호출)
- [ ] 기존 `publish-pypi.yml`을 공통 workflow 호출로 변경
- [ ] 테스트: workflow_dispatch로 release 실행
- [ ] 테스트: tag push 시 PyPI publish 확인

### 2.3 echo-server
- [ ] `release.yml` 추가 (공통 workflow 호출)
- [ ] 기존 `docker-push-on-tag.yml`을 공통 workflow 호출로 변경
- [ ] Secrets 이름 변경: `DOCKER_REGISTRY_*` → `DOCKER_*`
- [ ] 테스트: workflow_dispatch로 release 실행
- [ ] 테스트: tag push 시 docker 이미지 빌드 확인

### 2.4 inspireme.advenoh.pe.kr
- [ ] `release.yml` 추가 (공통 workflow 호출)
- [ ] 기존 `docker-push-on-tag.yml`을 공통 workflow 호출로 변경
- [ ] Secrets 이름 변경: `DOCKER_REGISTRY_*` → `DOCKER_*`
- [ ] 테스트: workflow_dispatch로 release 실행
- [ ] 테스트: tag push 시 docker 이미지 빌드 확인

### 2.5 toolbox
- [ ] `release.yml` 추가 (공통 workflow 호출)
- [ ] 기존 `docker-build.yml`을 공통 workflow 호출로 변경
- [ ] 테스트: workflow_dispatch로 release 실행
- [ ] 테스트: tag push 시 docker 이미지 빌드 확인

### 2.6 echo-http-cache
- [ ] `release.yml` 추가 (공통 workflow 호출, create_release: true)
- [ ] 테스트: workflow_dispatch로 release 실행
- [ ] GitHub Release 생성 확인

---

## Phase 3: 문서화

### 3.1 actions repo 문서화
- [x] `actions/README.md`에 새 workflow 사용법 추가
  - release.yml 사용법
  - docker-publish.yml 사용법
  - pypi-publish.yml 사용법
- [x] `actions/CLAUDE.md` 업데이트

### 3.2 각 repo 문서화
- [ ] stock-data-batch README에 release 방법 추가
- [ ] korea-investment-stock README에 release 방법 추가
- [ ] echo-server README에 release 방법 추가
- [ ] inspireme README에 release 방법 추가
- [ ] toolbox README에 release 방법 추가
- [ ] echo-http-cache README에 release 방법 추가

---

## Phase 4: Secrets 통일 (각 repo Settings에서)

### 4.1 echo-server
- [ ] `DOCKER_REGISTRY_USERNAME` → `DOCKER_USERNAME` 추가
- [ ] `DOCKER_REGISTRY_PASSWORD` → `DOCKER_PASSWORD` 추가
- [ ] 기존 secrets 삭제 (마이그레이션 완료 후)

### 4.2 inspireme.advenoh.pe.kr
- [ ] `DOCKER_REGISTRY_USERNAME` → `DOCKER_USERNAME` 추가
- [ ] `DOCKER_REGISTRY_PASSWORD` → `DOCKER_PASSWORD` 추가
- [ ] `DOCKER_REGISTRY_URL` 삭제 (기본값 docker.io 사용)
- [ ] 기존 secrets 삭제 (마이그레이션 완료 후)

---

## 완료 기준

- [ ] 모든 6개 repository에서 `workflow_dispatch`로 release 가능
- [ ] tag push 시 후속 작업(Docker/PyPI) 자동 실행
- [ ] 각 repo의 workflow 파일이 10줄 이내로 간소화
- [ ] 문서화 완료
