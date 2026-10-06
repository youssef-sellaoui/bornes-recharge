-- Communes écartées du classement : plus de 1,5 voiture par habitant.
-- Ce sont surtout des sièges de flottes (loueurs, entreprises, constructeurs),
-- mais aussi quelques tout petits villages où peu de voitures suffisent à dépasser le seuil.

SELECT v.codgeo AS code_commune,
       v.libgeo AS commune,
       v.nb_vp,
       p.population,
       ROUND(v.nb_vp::numeric / NULLIF(p.population::numeric, 0), 1) AS voitures_par_habitant
FROM voitures v
JOIN population p ON v.codgeo = p.code
WHERE v.date_arrete = '2025-09-30'
  AND v.nb_vp::numeric / NULLIF(p.population::numeric, 0) > 1.5
ORDER BY voitures_par_habitant DESC;
