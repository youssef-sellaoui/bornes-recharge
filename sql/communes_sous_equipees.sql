-- Communes avec au moins 100 voitures électriques
-- et au moins 1 point de recharge public,
-- classées par nombre de voitures électriques par point de recharge.
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
       v.nb_vp_rechargeables_el AS nb_ve,
       p.nb_points,
       ROUND(v.nb_vp_rechargeables_el::numeric / p.nb_points, 1) AS ve_par_point
FROM voitures v
JOIN points p ON v.codgeo = p.code_insee_commune
WHERE v.date_arrete = '2025-09-30'
  AND v.codgeo NOT IN (SELECT codgeo FROM flottes)
  AND v.nb_vp_rechargeables_el >= 100
ORDER BY ve_par_point DESC;
