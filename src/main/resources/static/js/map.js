(function () {
    const mapElement = document.getElementById("map");
    if (!mapElement) {
        return;
    }

    fetch("/api/workplaces")
        .then((response) => response.json())
        .then((workplaces) => {
            if (!window.kakao || !window.kakao.maps) {
                renderFallbackPins(workplaces);
                return;
            }

            const center = new kakao.maps.LatLng(35.1775, 126.9089);
            const map = new kakao.maps.Map(mapElement, {
                center: center,
                level: 4
            });

            workplaces.forEach((workplace) => {
                const markerNode = document.createElement("div");
                markerNode.className = "custom-marker " + workplace.markerColor;
                markerNode.title = workplace.name;

                const marker = new kakao.maps.CustomOverlay({
                    position: new kakao.maps.LatLng(workplace.latitude, workplace.longitude),
                    content: markerNode,
                    yAnchor: 1
                });

                markerNode.addEventListener("click", function () {
                    window.location.href = "/workplaces/" + workplace.id;
                });

                marker.setMap(map);
            });
        })
        .catch(() => {
            renderFallbackPins([]);
        });

    function renderFallbackPins(workplaces) {
        const fallback = mapElement.querySelector(".map-fallback");
        if (!fallback) {
            return;
        }

        const list = workplaces.map((workplace) => {
            const score = workplace.cleanScore === null ? "후기 부족" : Math.round(workplace.cleanScore) + "점";
            return `<a class="fallback-pin" href="/workplaces/${workplace.id}">
                <span class="dot ${workplace.markerColor}"></span>${workplace.name} · ${score}
            </a>`;
        }).join("");

        fallback.innerHTML = `<div class="fallback-list">
            <strong>Kakao Map API 키 연결 전 미리보기</strong>
            ${list || "<span>사업장 데이터를 불러오지 못했습니다.</span>"}
        </div>`;
    }
})();
