-- Communes avec au moins 100 voitures électriques
-- et AUCUN point de recharge public.
-- Les communes « sièges de flottes » (plus de 1,5 voiture par habitant) sont écartées.

WITH points AS (
    SELECT code_insee_commune, COUNT(*) AS nb_points
    FROM bornes
    GROUP BY code_insee_commune
),
flottes AS (
    SELECT v.codgeo
    FROM voitures v
    JOIN population p ON v.codgeo = p.code
    WHERE v.date_arrete = '2025-09-30'
      AND v.nb_vp::numeric / NULLIF(p.population::numeric, 0) > 1.5
)
SELECT v.codgeo AS code_commune,
       v.libgeo AS commune,
       v.nb_vp_rechargeables_el AS nb_ve
FROM voitures v
LEFT JOIN points p ON v.codgeo = p.code_insee_commune
WHERE v.date_arrete = '2025-09-30'
  AND v.codgeo NOT IN (SELECT codgeo FROM flottes)
  AND v.nb_vp_rechargeables_el >= 100
  AND p.nb_points IS NULL
  -- On garde seulement les codes qui existent encore en 2026 (liste de l'API).
  -- Les communes fusionnées ou renumérotées depuis (ex. Orée d'Anjou 49069 -> 49126)
  -- ont leurs bornes rangées sous le NOUVEAU code : elles sembleraient à tort « sans borne ».
  AND v.codgeo IN (SELECT code FROM population)
ORDER BY nb_ve DESC;
