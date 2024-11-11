# MPK Łódź

![icon2](https://github.com/user-attachments/assets/f781b344-b2f0-4107-873e-b159c66fdcb9)

Integracja do Homa Assistanta używające nieoficjalnego API [MPK Łódź](https://www.mpk.lodz.pl/) w celu pozyskania odjazdów na żywo autobusów i tramwajów. Integracja na bazie pracy [@PiotrMachowski](https://github.com/PiotrMachowski/Home-Assistant-custom-components-MPK-Lodz)

#### Instalacja

- Poprzez HACS (https://github.com/DominikWrobel/mpk_lodz) jako niestandardowe repozytorium

#### Użycie

Znajdź MPK Łódź w integracjach:

![konfiguracja](https://github.com/user-attachments/assets/c07bda54-d290-4cb9-8e08-61fd1413d892)

Możesz użyć stop_id, stop_numer albo grupę przystanków, aby znaleźć numer przystanku wejdź na stronę (http://rozklady.lodz.pl/) i znajdź swój przystanek, naciśnij na niego a znajdziesz numer przystanku:

![stopnr](https://github.com/user-attachments/assets/3f782c06-be82-40d0-a38a-af9ca50045ac)

Jeśli masz busStopNum= użyj pola numer, jeśli busStopId= użyj ID. Aby otrzymać grupę przystanków na stronie rozklady.lodz.pl trzeba zaznaczyć Węzły przystankowe i znaleźć swoją grupę:

![group](https://github.com/user-attachments/assets/431dadd6-453d-4966-a78e-355d195eabf5)


#### Dane

Po skonfigurowaniu integracji otrzymasz 10 encji, jedną na każdy odjazd z przystanku, w pierwszej encji otrzymasz dodatkowo dane o alertach oraz aktualnym czasie z systemu.

Dane są zoptymalizowane do użycia przez [custom:flex-table-card](https://github.com/custom-cards/flex-table-card) i można uzyskać taką kartę:

![pc](https://github.com/user-attachments/assets/9838b462-210e-4dfd-8657-5dbca5fba444)

<details>
<summary>Yaml</summary>
  
```
type: custom:flex-table-card
entities:
  include:
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_0
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_1
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_2
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_3
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_4
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_5
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_6
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_7
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_8
    - sensor.mpk_lodz_group_1_piotrkowska_centrum_9
columns:
  - name: " "
    icon: mdi:unicorn-variant
    data: line
    align: c
    modify: |-
      if (x.length == 0) {
       " ";
      } else {
        const lineNumber = parseInt(x);
        let icon = '';
        let style = '';
        switch(true) {
        case x.includes('N'):
          icon = 'mdi:bus';
          style = 'background-color: darkblue; color: lightgray;';
          break;
        case x.includes('6.'):
          icon = 'mdi:bus';
          style = 'color: green;';
          break;
        case !isNaN(lineNumber) && lineNumber >= 1 && lineNumber <= 49:
          icon = 'mdi:tram';
          style = 'color: orange;';
          break;
        case !isNaN(lineNumber) && lineNumber >= 50 && lineNumber <= 99:
          icon = 'mdi:bus';
          style = 'color: green;';
          break;
        case x.includes('Z'):
          icon = 'mdi:bus';
          style = 'color: green;';
          break;
        case x.includes('O'):
          icon = 'mdi:tram';
          style = 'color: orange;';
          break;
        case x.includes('100'):
          icon = 'mdi:bus';
          style = 'color: green;';
          break;
        case x.includes('151'):
          icon = 'mdi:bus';
          style = 'background-color: darkblue; color: lightgray;';
          break;
        case x.includes('102'):
          icon = 'mdi:bus';
          style = 'background-color: magenta; color: white;';
          break;
        case x.includes('C'):
          icon = 'mdi:tram';
          style = 'color: orange;';
          break;
        default:
          icon = 'mdi:bus';
      }
        '<div style="' + style + '"><ha-icon icon="' + icon + '"></ha-icon> ' + x + '</div>';
      }
  - name: Piotrkowska Centrum
    data: direction
    align: center
    modify: if(x.length == 0){" "}else{x}
  - name: " "
    icon: mdi:information-slab-circle-outline
    data: features
    align: c
  - name: " "
    data: time
    align: center
    modify: |-
      if (x.length == 0) {
        " ";
      } else {
        let style = '';
        let cssClass = '';
        if (x === '<1min') {
          style = 'color: red;';
          cssClass = 'blink';
        } else if (x.includes(':')) {
          style = 'color: lightgray;';
        } else {
          const minutes = parseInt(x);
          if (minutes === 1) {
            style = 'color: red;';
          } else if (minutes >= 2 && minutes <= 5) {
            style = 'color: yellow;';
          } else if (minutes >= 6) {
            style = 'color: green;';
          } else {
            style = 'color: gray;';
          }
        }
        '<div class="' + cssClass + '" style="' + style + '">' + x + '</div>';
      }
css:
  thead th:nth-child(1): "color: #4682B4;"
  thead th:nth-child(2): "color: #4682B4;"
  thead th:nth-child(3): "color: #4682B4;"
  thead th:nth-child(4): "color: #4682B4;"
  tbody tr td:nth-child(1)+: "min-width: 55px;width: 55px;"
  tbody tr td:nth-child(4)+: "min-width: 50px;width: 50px;"
  tbody tr td:nth-child(2)+: "min-width: 150px;width: 210px;"
  tbody tr td:nth-child(3)+: "min-width: 49px;width: 49px;"
  table+: "padding-bottom: 4px;"
  tbody tr:nth-child(even): "background-color: #a2542f6;"
  tbody tr:nth-child(odd): "background-color: #a2542f6;"
card_mod:
  style: |
    @keyframes blink {
      0% { opacity: 1; }
      50% { opacity: 0; }
      100% { opacity: 1; }
    }
    .blink {
      animation: blink 1s linear infinite;
    }
    ha-card {
      overflow: visible !important;
    }
    thead th:nth-child(4)::after {
      content: "{{ (state_attr("sensor.mpk_lodz_group_1_piotrkowska_centrum_0", "current_time")) }}";
    }
```
</details>

Dla alertów można użyć karty markdown (warunkowa):

![alert](https://github.com/user-attachments/assets/e8a93940-9ed7-4d06-8b62-be343501d1a7)

<details>
<summary>Yaml</summary>
  
```
type: markdown
content: >
  <center> {{ (state_attr("sensor.mpk_lodz_group_1_piotrkowska_centrum_0",
  "alert")) }} </center>
```
</details>

Można dodać dowolną liczbę przystaków. Alerty są wyświetlane jedynie dla przystanków z wyświetlaczami LED, aby uzyskać alert można dodać inny przystanek (np. Piotrkowska Centrum).


# Wsparcie:

Jeśli podoba Ci się moja integracja wesprzyj mnie poprzez:

<figure class="wp-block-image size-large"><a href="https://www.buymeacoffee.com/dominikjwrc"><img src="https://homeassistantwithoutaplan.files.wordpress.com/2023/07/coffe-3.png?w=182" alt="" class="wp-image-64"/></a></figure>
