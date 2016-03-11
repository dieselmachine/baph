# encoding: utf8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('DEPARTMENTS', 'MUNICIPALITIES')

DEPARTMENTS = (
  ('AMA', 'Amazonas'),
  ('ANT', 'Antioquia'),
  ('ARA', 'Arauca'),
  ('ATL', 'Atlántico'),
  ('DC', 'Bogotá'),
  ('BOL', 'Bolívar'),
  ('BOY', 'Boyacá'),
  ('CAL', 'Caldas'),
  ('CAQ', 'Caquetá'),
  ('CAS', 'Casanare'),
  ('CAU', 'Cauca'),
  ('CES', 'Cesar'),
  ('CHO', 'Chocó'),
  ('COR', 'Córdoba'),
  ('CUN', 'Cundinamarca'),
  ('GUA', 'Guainía'),
  ('GUV', 'Guaviare'),
  ('HUI', 'Huila'),
  ('LAG', 'La Guajira'),
  ('MAG', 'Magdalena'),
  ('MET', 'Meta'),
  ('NAR', 'Nariño'),
  ('NSA', 'Norte de Santander'),
  ('PUT', 'Putumayo'),
  ('QUI', 'Quindío'),
  ('RIS', 'Risaralda'),
  ('SAP', 'San Andrés and Providencia'),
  ('SAN', 'Santander'),
  ('SUC', 'Sucre'),
  ('TOL', 'Tolima'),
  ('VAC', 'Valle del Cauca'),
  ('VAU', 'Vaupés'),
  ('VID', 'Vichada'),
)

MUNICIPALITIES = (
  (1, 'El Encanto', 'AMA'),
  (2, 'La Chorrera', 'AMA'),
  (3, 'La Pedrera', 'AMA'),
  (4, 'La Victoria', 'AMA'),
  (5, 'Leticia', 'AMA'),
  (6, 'Miriti - Paraná', 'AMA'),
  (7, 'Puerto Alegría', 'AMA'),
  (8, 'Puerto Arica', 'AMA'),
  (9, 'Puerto Nariño', 'AMA'),
  (10, 'Puerto Santander', 'AMA'),
  (11, 'Tarapacá', 'AMA'),
  (12, 'Abejorral', 'ANT'),
  (13, 'Abriaquí', 'ANT'),
  (14, 'Alejandría', 'ANT'),
  (15, 'Amagá', 'ANT'),
  (16, 'Amalfi', 'ANT'),
  (17, 'Andes', 'ANT'),
  (18, 'Angelópolis', 'ANT'),
  (19, 'Angostura', 'ANT'),
  (20, 'Anorí', 'ANT'),
  (21, 'Anzá', 'ANT'),
  (22, 'Apartadó', 'ANT'),
  (23, 'Arboletes', 'ANT'),
  (24, 'Argelia', 'ANT'),
  (25, 'Armenia', 'ANT'),
  (26, 'Barbosa', 'ANT'),
  (27, 'Bello', 'ANT'),
  (28, 'Belmira', 'ANT'),
  (29, 'Betania', 'ANT'),
  (30, 'Betulia', 'ANT'),
  (31, 'Briceño', 'ANT'),
  (32, 'Buriticá', 'ANT'),
  (33, 'Caicedo', 'ANT'),
  (34, 'Caldas', 'ANT'),
  (35, 'Campamento', 'ANT'),
  (36, 'Caracolí', 'ANT'),
  (37, 'Caramanta', 'ANT'),
  (38, 'Carepa', 'ANT'),
  (39, 'Carolina del Príncipe', 'ANT'),
  (40, 'Caucasia', 'ANT'),
  (41, 'Cañasgordas', 'ANT'),
  (42, 'Chigorodó', 'ANT'),
  (43, 'Cisneros', 'ANT'),
  (44, 'Ciudad Bolívar', 'ANT'),
  (45, 'Cocorná', 'ANT'),
  (46, 'Concepción', 'ANT'),
  (47, 'Concordia', 'ANT'),
  (48, 'Copacabana', 'ANT'),
  (49, 'Cáceres', 'ANT'),
  (50, 'Dabeiba', 'ANT'),
  (51, 'Donmatías', 'ANT'),
  (52, 'Ebéjico', 'ANT'),
  (53, 'El Bagre', 'ANT'),
  (54, 'El Carmen de Viboral', 'ANT'),
  (55, 'El Santuario', 'ANT'),
  (56, 'Entrerríos', 'ANT'),
  (57, 'Envigado', 'ANT'),
  (58, 'Fredonia', 'ANT'),
  (59, 'Frontino', 'ANT'),
  (60, 'Giraldo', 'ANT'),
  (61, 'Girardota', 'ANT'),
  (62, 'Granada', 'ANT'),
  (63, 'Guadalupe', 'ANT'),
  (64, 'Guarne', 'ANT'),
  (65, 'Guatapé', 'ANT'),
  (66, 'Gómez Plata', 'ANT'),
  (67, 'Heliconia', 'ANT'),
  (68, 'Hispania', 'ANT'),
  (69, 'Itagüí', 'ANT'),
  (70, 'Ituango', 'ANT'),
  (71, 'Jardín', 'ANT'),
  (72, 'Jericó', 'ANT'),
  (73, 'La Ceja', 'ANT'),
  (74, 'La Estrella', 'ANT'),
  (75, 'La Pintada', 'ANT'),
  (76, 'La Unión', 'ANT'),
  (77, 'Liborina', 'ANT'),
  (78, 'Maceo', 'ANT'),
  (79, 'Marinilla', 'ANT'),
  (80, 'Medellín', 'ANT'),
  (81, 'Montebello', 'ANT'),
  (82, 'Murindó', 'ANT'),
  (83, 'Mutatá', 'ANT'),
  (84, 'Nariño', 'ANT'),
  (85, 'Nechí', 'ANT'),
  (86, 'Necoclí', 'ANT'),
  (87, 'Olaya', 'ANT'),
  (88, 'Peque', 'ANT'),
  (89, 'Peñol', 'ANT'),
  (90, 'Pueblorrico', 'ANT'),
  (91, 'Puerto Berrío', 'ANT'),
  (92, 'Puerto Nare', 'ANT'),
  (93, 'Puerto Triunfo', 'ANT'),
  (94, 'Remedios', 'ANT'),
  (95, 'Retiro', 'ANT'),
  (96, 'Rionegro', 'ANT'),
  (97, 'Sabanalarga', 'ANT'),
  (98, 'Sabaneta', 'ANT'),
  (99, 'Salgar', 'ANT'),
  (100, 'San Andrés de Cuerquía', 'ANT'),
  (101, 'San Carlos', 'ANT'),
  (102, 'San Francisco', 'ANT'),
  (103, 'San Jerónimo', 'ANT'),
  (104, 'San José de La Montaña', 'ANT'),
  (105, 'San Juan de Urabá', 'ANT'),
  (106, 'San Luis', 'ANT'),
  (107, 'San Pedro', 'ANT'),
  (108, 'San Pedro de Urabá', 'ANT'),
  (109, 'San Rafael', 'ANT'),
  (110, 'San Roque', 'ANT'),
  (111, 'San Vicente', 'ANT'),
  (112, 'Santa Bárbara', 'ANT'),
  (113, 'Santa Fe de Antioquia', 'ANT'),
  (114, 'Santa Rosa de Osos', 'ANT'),
  (115, 'Santo Domingo', 'ANT'),
  (116, 'Segovia', 'ANT'),
  (117, 'Sonsón', 'ANT'),
  (118, 'Sopetrán', 'ANT'),
  (119, 'Tarazá', 'ANT'),
  (120, 'Tarso', 'ANT'),
  (121, 'Titiribí', 'ANT'),
  (122, 'Toledo', 'ANT'),
  (123, 'Turbo', 'ANT'),
  (124, 'Támesis', 'ANT'),
  (125, 'Uramita', 'ANT'),
  (126, 'Urrao', 'ANT'),
  (127, 'Valdivia', 'ANT'),
  (128, 'Valparaíso', 'ANT'),
  (129, 'Vegachí', 'ANT'),
  (130, 'Venecia', 'ANT'),
  (131, 'Vigía del Fuerte', 'ANT'),
  (132, 'Yalí', 'ANT'),
  (133, 'Yarumal', 'ANT'),
  (134, 'Yolombó', 'ANT'),
  (135, 'Yondó', 'ANT'),
  (136, 'Zaragoza', 'ANT'),
  (137, 'Arauca', 'ARA'),
  (138, 'Arauquita', 'ARA'),
  (139, 'Cravo Norte', 'ARA'),
  (140, 'Fortul', 'ARA'),
  (141, 'Puerto Rondón', 'ARA'),
  (142, 'Saravena', 'ARA'),
  (143, 'Tame', 'ARA'),
  (144, 'San Andrés', 'SAP'),
  (145, 'Santa Isabel', 'SAP'),
  (146, 'Baranoa', 'ATL'),
  (147, 'Barranquilla', 'ATL'),
  (148, 'Campo de La Cruz', 'ATL'),
  (149, 'Candelaria', 'ATL'),
  (150, 'Galapa', 'ATL'),
  (151, 'Juan de Acosta', 'ATL'),
  (152, 'Luruaco', 'ATL'),
  (153, 'Malambo', 'ATL'),
  (154, 'Manatí', 'ATL'),
  (155, 'Palmar de Varela', 'ATL'),
  (156, 'Piojó', 'ATL'),
  (157, 'Polonuevo', 'ATL'),
  (158, 'Ponedera', 'ATL'),
  (159, 'Puerto Colombia', 'ATL'),
  (160, 'Repelón', 'ATL'),
  (161, 'Sabanagrande', 'ATL'),
  (162, 'Sabanalarga', 'ATL'),
  (163, 'Santa Lucía', 'ATL'),
  (164, 'Santo Tomás', 'ATL'),
  (165, 'Soledad', 'ATL'),
  (166, 'Suan', 'ATL'),
  (167, 'Tubará', 'ATL'),
  (168, 'Usiacurí', 'ATL'),
  (169, 'Bogotá', 'DC'),
  (170, 'Achí', 'BOL'),
  (171, 'Altos del Rosario', 'BOL'),
  (172, 'Arenal del Sur', 'BOL'),
  (173, 'Arjona', 'BOL'),
  (174, 'Arroyohondo', 'BOL'),
  (175, 'Barranco de Loba', 'BOL'),
  (176, 'Calamar', 'BOL'),
  (177, 'Cantagallo', 'BOL'),
  (178, 'Cartagena', 'BOL'),
  (179, 'Cicuco', 'BOL'),
  (180, 'Clemencia', 'BOL'),
  (181, 'Córdoba', 'BOL'),
  (182, 'El Carmen de Bolívar', 'BOL'),
  (183, 'El Guamo', 'BOL'),
  (184, 'El Peñón', 'BOL'),
  (185, 'Hatillo de Loba', 'BOL'),
  (186, 'Magangué', 'BOL'),
  (187, 'Mahates', 'BOL'),
  (188, 'Margarita', 'BOL'),
  (189, 'María La Baja', 'BOL'),
  (190, 'Mompós (Santa Cruz de Mompós)', 'BOL'),
  (191, 'Montecristo', 'BOL'),
  (192, 'Morales', 'BOL'),
  (193, 'Norosí (← Río Viejo)', 'BOL'),
  (194, 'Pinillos', 'BOL'),
  (195, 'Regidor', 'BOL'),
  (196, 'Río Viejo', 'BOL'),
  (197, 'San Cristóbal', 'BOL'),
  (198, 'San Estanislao', 'BOL'),
  (199, 'San Fernando', 'BOL'),
  (200, 'San Jacinto', 'BOL'),
  (201, 'San Jacinto del Cauca', 'BOL'),
  (202, 'San Juan Nepomuceno', 'BOL'),
  (203, 'San Martín de Loba', 'BOL'),
  (204, 'San Pablo', 'BOL'),
  (205, 'Santa Catalina', 'BOL'),
  (206, 'Santa Rosa', 'BOL'),
  (207, 'Santa Rosa del Sur', 'BOL'),
  (208, 'Simití', 'BOL'),
  (209, 'Soplaviento', 'BOL'),
  (210, 'Talaigua Nuevo', 'BOL'),
  (211, 'Tiquisio', 'BOL'),
  (212, 'Turbaco', 'BOL'),
  (213, 'Turbaná', 'BOL'),
  (214, 'Villanueva', 'BOL'),
  (215, 'Zambrano', 'BOL'),
  (216, 'Almeida', 'BOY'),
  (217, 'Aquitania', 'BOY'),
  (218, 'Arcabuco', 'BOY'),
  (219, 'Belén', 'BOY'),
  (220, 'Berbeo', 'BOY'),
  (221, 'Betéitiva', 'BOY'),
  (222, 'Boavita', 'BOY'),
  (223, 'Boyacá', 'BOY'),
  (224, 'Briceño', 'BOY'),
  (225, 'Buenavista', 'BOY'),
  (226, 'Busbanzá', 'BOY'),
  (227, 'Caldas', 'BOY'),
  (228, 'Campohermoso', 'BOY'),
  (229, 'Cerinza', 'BOY'),
  (230, 'Chinavita', 'BOY'),
  (231, 'Chiquinquirá', 'BOY'),
  (232, 'Chiscas', 'BOY'),
  (233, 'Chita', 'BOY'),
  (234, 'Chitaraque', 'BOY'),
  (235, 'Chivatá', 'BOY'),
  (236, 'Chivor', 'BOY'),
  (237, 'Chíquiza', 'BOY'),
  (238, 'Ciénega', 'BOY'),
  (239, 'Coper', 'BOY'),
  (240, 'Corrales', 'BOY'),
  (241, 'Covarachía', 'BOY'),
  (242, 'Cubará', 'BOY'),
  (243, 'Cucaita', 'BOY'),
  (244, 'Cuítiva', 'BOY'),
  (245, 'Cómbita', 'BOY'),
  (246, 'Duitama', 'BOY'),
  (247, 'El Cocuy', 'BOY'),
  (248, 'El Espino', 'BOY'),
  (249, 'Firavitoba', 'BOY'),
  (250, 'Floresta', 'BOY'),
  (251, 'Gachantivá', 'BOY'),
  (252, 'Garagoa', 'BOY'),
  (253, 'Guacamayas', 'BOY'),
  (254, 'Guateque', 'BOY'),
  (255, 'Guayatá', 'BOY'),
  (256, 'Gámeza', 'BOY'),
  (257, 'Güicán', 'BOY'),
  (258, 'Iza', 'BOY'),
  (259, 'Jenesano', 'BOY'),
  (260, 'Jericó', 'BOY'),
  (261, 'La Capilla', 'BOY'),
  (262, 'La Uvita', 'BOY'),
  (263, 'La Victoria', 'BOY'),
  (264, 'Labranzagrande', 'BOY'),
  (265, 'Macanal', 'BOY'),
  (266, 'Maripí', 'BOY'),
  (267, 'Miraflores', 'BOY'),
  (268, 'Mongua', 'BOY'),
  (269, 'Monguí', 'BOY'),
  (270, 'Moniquirá', 'BOY'),
  (271, 'Motavita', 'BOY'),
  (272, 'Muzo', 'BOY'),
  (273, 'Nobsa', 'BOY'),
  (274, 'Nuevo Colón', 'BOY'),
  (275, 'Oicatá', 'BOY'),
  (276, 'Otanche', 'BOY'),
  (277, 'Pachavita', 'BOY'),
  (278, 'Paipa', 'BOY'),
  (279, 'Pajarito', 'BOY'),
  (280, 'Panqueba', 'BOY'),
  (281, 'Pauna', 'BOY'),
  (282, 'Paya', 'BOY'),
  (283, 'Paz de Río', 'BOY'),
  (284, 'Pesca', 'BOY'),
  (285, 'Pisba', 'BOY'),
  (286, 'Puerto Boyacá', 'BOY'),
  (287, 'Páez', 'BOY'),
  (288, 'Quípama', 'BOY'),
  (289, 'Ramiriquí', 'BOY'),
  (290, 'Rondón', 'BOY'),
  (291, 'Ráquira', 'BOY'),
  (292, 'Saboyá', 'BOY'),
  (293, 'Samacá', 'BOY'),
  (294, 'San Eduardo', 'BOY'),
  (295, 'San José de Pare', 'BOY'),
  (296, 'San Luis de Gaceno', 'BOY'),
  (297, 'San Mateo', 'BOY'),
  (298, 'San Miguel de Sema', 'BOY'),
  (299, 'San Pablo de Borbur', 'BOY'),
  (300, 'Santa María', 'BOY'),
  (301, 'Santa Rosa de Viterbo', 'BOY'),
  (302, 'Santa Sofía', 'BOY'),
  (303, 'Santana', 'BOY'),
  (304, 'Sativanorte', 'BOY'),
  (305, 'Sativasur', 'BOY'),
  (306, 'Siachoque', 'BOY'),
  (307, 'Soatá', 'BOY'),
  (308, 'Socha', 'BOY'),
  (309, 'Socotá', 'BOY'),
  (310, 'Sogamoso', 'BOY'),
  (311, 'Somondoco', 'BOY'),
  (312, 'Sora', 'BOY'),
  (313, 'Soracá', 'BOY'),
  (314, 'Sotaquirá', 'BOY'),
  (315, 'Susacón', 'BOY'),
  (316, 'Sutamarchán', 'BOY'),
  (317, 'Sutatenza', 'BOY'),
  (318, 'Sáchica', 'BOY'),
  (319, 'Tasco', 'BOY'),
  (320, 'Tenza', 'BOY'),
  (321, 'Tibaná', 'BOY'),
  (322, 'Tibasosa', 'BOY'),
  (323, 'Tinjacá', 'BOY'),
  (324, 'Tipacoque', 'BOY'),
  (325, 'Toca', 'BOY'),
  (326, 'Togüí', 'BOY'),
  (327, 'Tota', 'BOY'),
  (328, 'Tunja', 'BOY'),
  (329, 'Tununguá', 'BOY'),
  (330, 'Turmequé', 'BOY'),
  (331, 'Tuta', 'BOY'),
  (332, 'Tutazá', 'BOY'),
  (333, 'Tópaga', 'BOY'),
  (334, 'Ventaquemada', 'BOY'),
  (335, 'Villa de Leyva', 'BOY'),
  (336, 'Viracachá', 'BOY'),
  (337, 'Zetaquira', 'BOY'),
  (338, 'Úmbita', 'BOY'),
  (339, 'Aguadas', 'CAL'),
  (340, 'Anserma', 'CAL'),
  (341, 'Aranzazu', 'CAL'),
  (342, 'Belalcázar', 'CAL'),
  (343, 'Chinchiná', 'CAL'),
  (344, 'Filadelfia', 'CAL'),
  (345, 'La Dorada', 'CAL'),
  (346, 'La Merced', 'CAL'),
  (347, 'Manizales', 'CAL'),
  (348, 'Manzanares', 'CAL'),
  (349, 'Marmato', 'CAL'),
  (350, 'Marquetalia', 'CAL'),
  (351, 'Marulanda', 'CAL'),
  (352, 'Neira', 'CAL'),
  (353, 'Norcasia', 'CAL'),
  (354, 'Palestina', 'CAL'),
  (355, 'Pensilvania', 'CAL'),
  (356, 'Pácora', 'CAL'),
  (357, 'Riosucio', 'CAL'),
  (358, 'Risaralda', 'CAL'),
  (359, 'Salamina', 'CAL'),
  (360, 'Samaná', 'CAL'),
  (361, 'San José', 'CAL'),
  (362, 'Supía', 'CAL'),
  (363, 'Victoria', 'CAL'),
  (364, 'Villamaría', 'CAL'),
  (365, 'Viterbo', 'CAL'),
  (366, 'Albania', 'CAQ'),
  (367, 'Belén de los Andaquíes', 'CAQ'),
  (368, 'Cartagena del Chairá', 'CAQ'),
  (369, 'Curillo', 'CAQ'),
  (370, 'El Doncello', 'CAQ'),
  (371, 'El Paujíl', 'CAQ'),
  (372, 'Florencia', 'CAQ'),
  (373, 'La Montañita', 'CAQ'),
  (374, 'Milán', 'CAQ'),
  (375, 'Morelia', 'CAQ'),
  (376, 'Puerto Rico', 'CAQ'),
  (377, 'San José del Fragua', 'CAQ'),
  (378, 'San Vicente del Caguán', 'CAQ'),
  (379, 'Solano', 'CAQ'),
  (380, 'Solita', 'CAQ'),
  (381, 'Valparaíso', 'CAQ'),
  (382, 'Aguazul', 'CAS'),
  (383, 'Chámeza', 'CAS'),
  (384, 'Hato Corozal', 'CAS'),
  (385, 'La Salina', 'CAS'),
  (386, 'Maní', 'CAS'),
  (387, 'Monterrey', 'CAS'),
  (388, 'Nunchía', 'CAS'),
  (389, 'Orocué', 'CAS'),
  (390, 'Paz de Ariporo', 'CAS'),
  (391, 'Pore', 'CAS'),
  (392, 'Recetor', 'CAS'),
  (393, 'Sabanalarga', 'CAS'),
  (394, 'San Luis de Palenque', 'CAS'),
  (395, 'Sácama', 'CAS'),
  (396, 'Tauramena', 'CAS'),
  (397, 'Trinidad', 'CAS'),
  (398, 'Támara', 'CAS'),
  (399, 'Villanueva', 'CAS'),
  (400, 'Yopal', 'CAS'),
  (401, 'Almaguer', 'CAU'),
  (402, 'Argelia', 'CAU'),
  (403, 'Balboa', 'CAU'),
  (404, 'Bolívar', 'CAU'),
  (405, 'Buenos Aires', 'CAU'),
  (406, 'Cajibío', 'CAU'),
  (407, 'Caldono', 'CAU'),
  (408, 'Caloto', 'CAU'),
  (409, 'Corinto', 'CAU'),
  (410, 'El Tambo', 'CAU'),
  (411, 'Florencia', 'CAU'),
  (412, 'Guachené (← Caloto)', 'CAU'),
  (413, 'Guapí', 'CAU'),
  (414, 'Inzá', 'CAU'),
  (415, 'Jambaló', 'CAU'),
  (416, 'La Sierra', 'CAU'),
  (417, 'La Vega', 'CAU'),
  (418, 'López de Micay', 'CAU'),
  (419, 'Mercaderes', 'CAU'),
  (420, 'Miranda', 'CAU'),
  (421, 'Morales', 'CAU'),
  (422, 'Padilla', 'CAU'),
  (423, 'Patía', 'CAU'),
  (424, 'Piamonte', 'CAU'),
  (425, 'Piendamó', 'CAU'),
  (426, 'Popayán', 'CAU'),
  (427, 'Puerto Tejada', 'CAU'),
  (428, 'Puracé', 'CAU'),
  (429, 'Páez', 'CAU'),
  (430, 'Rosas', 'CAU'),
  (431, 'San Sebastián', 'CAU'),
  (432, 'Santa Rosa', 'CAU'),
  (433, 'Santander de Quilichao', 'CAU'),
  (434, 'Silvia', 'CAU'),
  (435, 'Sotará', 'CAU'),
  (436, 'Sucre', 'CAU'),
  (437, 'Suárez', 'CAU'),
  (438, 'Timbiquí', 'CAU'),
  (439, 'Timbío', 'CAU'),
  (440, 'Toribío', 'CAU'),
  (441, 'Totoró', 'CAU'),
  (442, 'Villa Rica', 'CAU'),
  (443, 'Aguachica', 'CES'),
  (444, 'Agustín Codazzi', 'CES'),
  (445, 'Astrea', 'CES'),
  (446, 'Becerril', 'CES'),
  (447, 'Bosconia', 'CES'),
  (448, 'Chimichagua', 'CES'),
  (449, 'Chiriguaná', 'CES'),
  (450, 'Curumaní', 'CES'),
  (451, 'El Copey', 'CES'),
  (452, 'El Paso', 'CES'),
  (453, 'Gamarra', 'CES'),
  (454, 'González', 'CES'),
  (455, 'La Gloria', 'CES'),
  (456, 'La Jagua de Ibirico', 'CES'),
  (457, 'La Paz', 'CES'),
  (458, 'Manaure', 'CES'),
  (459, 'Pailitas', 'CES'),
  (460, 'Pelaya', 'CES'),
  (461, 'Pueblo Bello', 'CES'),
  (462, 'Río de Oro', 'CES'),
  (463, 'San Alberto', 'CES'),
  (464, 'San Diego', 'CES'),
  (465, 'San Martín', 'CES'),
  (466, 'Tamalameque', 'CES'),
  (467, 'Valledupar', 'CES'),
  (468, 'Acandí', 'CHO'),
  (469, 'Alto Baudó', 'CHO'),
  (470, 'Atrato', 'CHO'),
  (471, 'Bagadó', 'CHO'),
  (472, 'Bahía Solano', 'CHO'),
  (473, 'Bajo Baudó', 'CHO'),
  (474, 'Bojayá', 'CHO'),
  (475, 'Carmen del Darién', 'CHO'),
  (476, 'Condoto', 'CHO'),
  (477, 'Cértegui', 'CHO'),
  (478, 'El Cantón de San Pablo', 'CHO'),
  (479, 'El Carmen de Atrato', 'CHO'),
  (480, 'El Litoral del San Juan', 'CHO'),
  (481, 'Istmina', 'CHO'),
  (482, 'Juradó', 'CHO'),
  (483, 'Lloró', 'CHO'),
  (484, 'Medio Atrato', 'CHO'),
  (485, 'Medio Baudó', 'CHO'),
  (486, 'Medio San Juan', 'CHO'),
  (487, 'Nuquí', 'CHO'),
  (488, 'Nóvita', 'CHO'),
  (489, 'Quibdó', 'CHO'),
  (490, 'Riosucio', 'CHO'),
  (491, 'Río Iró', 'CHO'),
  (492, 'Río Quito', 'CHO'),
  (493, 'San José del Palmar', 'CHO'),
  (494, 'Sipí', 'CHO'),
  (495, 'Tadó', 'CHO'),
  (496, 'Unguía', 'CHO'),
  (497, 'Unión Panamericana', 'CHO'),
  (498, 'Agua de Dios', 'CUN'),
  (499, 'Albán', 'CUN'),
  (500, 'Anapoima', 'CUN'),
  (501, 'Anolaima', 'CUN'),
  (502, 'Apulo', 'CUN'),
  (503, 'Arbeláez', 'CUN'),
  (504, 'Beltrán', 'CUN'),
  (505, 'Bituima', 'CUN'),
  (506, 'Bojacá', 'CUN'),
  (507, 'Cabrera', 'CUN'),
  (508, 'Cachipay', 'CUN'),
  (509, 'Cajicá', 'CUN'),
  (510, 'Caparrapí', 'CUN'),
  (511, 'Carmen de Carupa', 'CUN'),
  (512, 'Chaguaní', 'CUN'),
  (513, 'Chipaque', 'CUN'),
  (514, 'Choachí', 'CUN'),
  (515, 'Chocontá', 'CUN'),
  (516, 'Chía', 'CUN'),
  (517, 'Cogua', 'CUN'),
  (518, 'Cota', 'CUN'),
  (519, 'Cucunubá', 'CUN'),
  (520, 'Cáqueza', 'CUN'),
  (521, 'El Colegio', 'CUN'),
  (522, 'El Peñón', 'CUN'),
  (523, 'El Rosal', 'CUN'),
  (524, 'Facatativá', 'CUN'),
  (525, 'Fosca', 'CUN'),
  (526, 'Funza', 'CUN'),
  (527, 'Fusagasugá', 'CUN'),
  (528, 'Fómeque', 'CUN'),
  (529, 'Fúquene', 'CUN'),
  (530, 'Gachalá', 'CUN'),
  (531, 'Gachancipá', 'CUN'),
  (532, 'Gachetá', 'CUN'),
  (533, 'Gama', 'CUN'),
  (534, 'Girardot', 'CUN'),
  (535, 'Granada', 'CUN'),
  (536, 'Guachetá', 'CUN'),
  (537, 'Guaduas', 'CUN'),
  (538, 'Guasca', 'CUN'),
  (539, 'Guataquí', 'CUN'),
  (540, 'Guatavita', 'CUN'),
  (541, 'Guayabal de Síquima', 'CUN'),
  (542, 'Guayabetal', 'CUN'),
  (543, 'Gutiérrez', 'CUN'),
  (544, 'Jerusalén', 'CUN'),
  (545, 'Junín', 'CUN'),
  (546, 'La Calera', 'CUN'),
  (547, 'La Mesa', 'CUN'),
  (548, 'La Palma', 'CUN'),
  (549, 'La Peña', 'CUN'),
  (550, 'La Vega', 'CUN'),
  (551, 'Lenguazaque', 'CUN'),
  (552, 'Machetá', 'CUN'),
  (553, 'Madrid', 'CUN'),
  (554, 'Manta', 'CUN'),
  (555, 'Medina', 'CUN'),
  (556, 'Mosquera', 'CUN'),
  (557, 'Nariño', 'CUN'),
  (558, 'Nemocón', 'CUN'),
  (559, 'Nilo', 'CUN'),
  (560, 'Nimaima', 'CUN'),
  (561, 'Nocaima', 'CUN'),
  (562, 'Pacho', 'CUN'),
  (563, 'Paime', 'CUN'),
  (564, 'Pandi', 'CUN'),
  (565, 'Paratebueno', 'CUN'),
  (566, 'Pasca', 'CUN'),
  (567, 'Puerto Salgar', 'CUN'),
  (568, 'Pulí', 'CUN'),
  (569, 'Quebradanegra', 'CUN'),
  (570, 'Quetame', 'CUN'),
  (571, 'Quipile', 'CUN'),
  (572, 'Ricaurte', 'CUN'),
  (573, 'San Antonio del Tequendama', 'CUN'),
  (574, 'San Bernardo', 'CUN'),
  (575, 'San Cayetano', 'CUN'),
  (576, 'San Francisco', 'CUN'),
  (577, 'San Juan de Rioseco', 'CUN'),
  (578, 'Sasaima', 'CUN'),
  (579, 'Sesquilé', 'CUN'),
  (580, 'Sibaté', 'CUN'),
  (581, 'Silvania', 'CUN'),
  (582, 'Simijaca', 'CUN'),
  (583, 'Soacha', 'CUN'),
  (584, 'Sopó', 'CUN'),
  (585, 'Subachoque', 'CUN'),
  (586, 'Suesca', 'CUN'),
  (587, 'Supatá', 'CUN'),
  (588, 'Susa', 'CUN'),
  (589, 'Sutatausa', 'CUN'),
  (590, 'Tabio', 'CUN'),
  (591, 'Tausa', 'CUN'),
  (592, 'Tena', 'CUN'),
  (593, 'Tenjo', 'CUN'),
  (594, 'Tibacuy', 'CUN'),
  (595, 'Tibirita', 'CUN'),
  (596, 'Tocaima', 'CUN'),
  (597, 'Tocancipá', 'CUN'),
  (598, 'Topaipí', 'CUN'),
  (599, 'Ubalá', 'CUN'),
  (600, 'Ubaque', 'CUN'),
  (601, 'Ubaté', 'CUN'),
  (602, 'Une', 'CUN'),
  (603, 'Venecia', 'CUN'),
  (604, 'Vergara', 'CUN'),
  (605, 'Vianí', 'CUN'),
  (606, 'Villagómez', 'CUN'),
  (607, 'Villapinzón', 'CUN'),
  (608, 'Villeta', 'CUN'),
  (609, 'Viotá', 'CUN'),
  (610, 'Yacopí', 'CUN'),
  (611, 'Zipacón', 'CUN'),
  (612, 'Zipaquirá', 'CUN'),
  (613, 'Útica', 'CUN'),
  (614, 'Ayapel', 'COR'),
  (615, 'Buenavista', 'COR'),
  (616, 'Canalete', 'COR'),
  (617, 'Cereté', 'COR'),
  (618, 'Chimá', 'COR'),
  (619, 'Chinú', 'COR'),
  (620, 'Ciénaga de Oro', 'COR'),
  (621, 'Cotorra', 'COR'),
  (622, 'La Apartada', 'COR'),
  (623, 'Los Córdobas', 'COR'),
  (624, 'Momil', 'COR'),
  (625, 'Montelíbano', 'COR'),
  (626, 'Montería', 'COR'),
  (627, 'Moñitos', 'COR'),
  (628, 'Planeta Rica', 'COR'),
  (629, 'Pueblo Nuevo', 'COR'),
  (630, 'Puerto Escondido', 'COR'),
  (631, 'Puerto Libertador', 'COR'),
  (632, 'Purísima de la Concepción', 'COR'),
  (633, 'Sahagún', 'COR'),
  (634, 'San Andrés de Sotavento', 'COR'),
  (635, 'San Antero', 'COR'),
  (636, 'San Bernardo del Viento', 'COR'),
  (637, 'San Carlos', 'COR'),
  (638, 'San José de Uré (← Montelíbano)', 'COR'),
  (639, 'San Pelayo', 'COR'),
  (640, 'Santa Cruz de Lorica', 'COR'),
  (641, 'Tierralta', 'COR'),
  (642, 'Tuchín (← San Andrés de Sotavento)', 'COR'),
  (643, 'Valencia', 'COR'),
  (644, 'Barranco Minas', 'GUA'),
  (645, 'Cacahual', 'GUA'),
  (646, 'Inírida', 'GUA'),
  (647, 'La Guadalupe', 'GUA'),
  (648, 'Mapiripana', 'GUA'),
  (649, 'Morichal Nuevo', 'GUA'),
  (650, 'Pana Pana', 'GUA'),
  (651, 'Puerto Colombia', 'GUA'),
  (652, 'San Felipe', 'GUA'),
  (653, 'Calamar', 'GUV'),
  (654, 'El Retorno', 'GUV'),
  (655, 'Miraflores', 'GUV'),
  (656, 'San José del Guaviare', 'GUV'),
  (657, 'Acevedo', 'HUI'),
  (658, 'Agrado', 'HUI'),
  (659, 'Aipe', 'HUI'),
  (660, 'Algeciras', 'HUI'),
  (661, 'Altamira', 'HUI'),
  (662, 'Baraya', 'HUI'),
  (663, 'Campoalegre', 'HUI'),
  (664, 'Colombia', 'HUI'),
  (665, 'Elías', 'HUI'),
  (666, 'Garzón', 'HUI'),
  (667, 'Gigante', 'HUI'),
  (668, 'Guadalupe', 'HUI'),
  (669, 'Hobo', 'HUI'),
  (670, 'Isnos', 'HUI'),
  (671, 'La Argentina', 'HUI'),
  (672, 'La Plata', 'HUI'),
  (673, 'Neiva', 'HUI'),
  (674, 'Nátaga', 'HUI'),
  (675, 'Oporapa', 'HUI'),
  (676, 'Paicol', 'HUI'),
  (677, 'Palermo', 'HUI'),
  (678, 'Palestina', 'HUI'),
  (679, 'Pital', 'HUI'),
  (680, 'Pitalito', 'HUI'),
  (681, 'Rivera', 'HUI'),
  (682, 'Saladoblanco', 'HUI'),
  (683, 'San Agustín', 'HUI'),
  (684, 'Santa María', 'HUI'),
  (685, 'Suaza', 'HUI'),
  (686, 'Tarqui', 'HUI'),
  (687, 'Tello', 'HUI'),
  (688, 'Teruel', 'HUI'),
  (689, 'Tesalia', 'HUI'),
  (690, 'Timaná', 'HUI'),
  (691, 'Villavieja', 'HUI'),
  (692, 'Yaguará', 'HUI'),
  (693, 'Íquira', 'HUI'),
  (694, 'Albania', 'LAG'),
  (695, 'Barrancas', 'LAG'),
  (696, 'Dibulla', 'LAG'),
  (697, 'Distracción', 'LAG'),
  (698, 'El Molino', 'LAG'),
  (699, 'Fonseca', 'LAG'),
  (700, 'Hatonuevo', 'LAG'),
  (701, 'La Jagua del Pilar', 'LAG'),
  (702, 'Maicao', 'LAG'),
  (703, 'Manaure', 'LAG'),
  (704, 'Riohacha', 'LAG'),
  (705, 'San Juan del Cesar', 'LAG'),
  (706, 'Uribia', 'LAG'),
  (707, 'Urumita', 'LAG'),
  (708, 'Villanueva', 'LAG'),
  (709, 'Algarrobo', 'MAG'),
  (710, 'Aracataca', 'MAG'),
  (711, 'Ariguaní', 'MAG'),
  (712, 'Cerro de San Antonio', 'MAG'),
  (713, 'Chibolo (Chivolo)', 'MAG'),
  (714, 'Ciénaga', 'MAG'),
  (715, 'Concordia', 'MAG'),
  (716, 'El Banco', 'MAG'),
  (717, 'El Piñón', 'MAG'),
  (718, 'El Retén', 'MAG'),
  (719, 'Fundación', 'MAG'),
  (720, 'Guamal', 'MAG'),
  (721, 'Nueva Granada', 'MAG'),
  (722, 'Pedraza', 'MAG'),
  (723, 'Pijiño del Carmen', 'MAG'),
  (724, 'Pivijay', 'MAG'),
  (725, 'Plato', 'MAG'),
  (726, 'Pueblo Viejo', 'MAG'),
  (727, 'Remolino', 'MAG'),
  (728, 'Sabanas de San Ángel', 'MAG'),
  (729, 'Salamina', 'MAG'),
  (730, 'San Sebastián de Buenavista', 'MAG'),
  (731, 'San Zenón', 'MAG'),
  (732, 'Santa Ana', 'MAG'),
  (733, 'Santa Bárbara de Pinto', 'MAG'),
  (734, 'Santa Marta', 'MAG'),
  (735, 'Sitionuevo', 'MAG'),
  (736, 'Tenerife', 'MAG'),
  (737, 'Zapayán', 'MAG'),
  (738, 'Zona Bananera', 'MAG'),
  (739, 'Acacías', 'MET'),
  (740, 'Barranca de Upía', 'MET'),
  (741, 'Cabuyaro', 'MET'),
  (742, 'Castilla la Nueva', 'MET'),
  (743, 'Cumaral', 'MET'),
  (744, 'El Calvario', 'MET'),
  (745, 'El Castillo', 'MET'),
  (746, 'El Dorado', 'MET'),
  (747, 'Fuente de Oro', 'MET'),
  (748, 'Granada', 'MET'),
  (749, 'Guamal', 'MET'),
  (750, 'La Macarena', 'MET'),
  (751, 'La Uribe', 'MET'),
  (752, 'Lejanías', 'MET'),
  (753, 'Mapiripán', 'MET'),
  (754, 'Mesetas', 'MET'),
  (755, 'Puerto Concordia', 'MET'),
  (756, 'Puerto Gaitán', 'MET'),
  (757, 'Puerto Lleras', 'MET'),
  (758, 'Puerto López', 'MET'),
  (759, 'Puerto Rico', 'MET'),
  (760, 'Restrepo', 'MET'),
  (761, 'San Carlos de Guaroa', 'MET'),
  (762, 'San Juan de Arama', 'MET'),
  (763, 'San Juanito', 'MET'),
  (764, 'San Luis de Cubarral', 'MET'),
  (765, 'San Martín', 'MET'),
  (766, 'Villavicencio', 'MET'),
  (767, 'Vista Hermosa', 'MET'),
  (768, 'Albán', 'NAR'),
  (769, 'Aldana', 'NAR'),
  (770, 'Ancuyá', 'NAR'),
  (771, 'Arboleda', 'NAR'),
  (772, 'Barbacoas', 'NAR'),
  (773, 'Belén', 'NAR'),
  (774, 'Buesaco', 'NAR'),
  (775, 'Chachagüí', 'NAR'),
  (776, 'Colón', 'NAR'),
  (777, 'Consacá', 'NAR'),
  (778, 'Contadero', 'NAR'),
  (779, 'Cuaspud', 'NAR'),
  (780, 'Cumbal', 'NAR'),
  (781, 'Cumbitara', 'NAR'),
  (782, 'Córdoba', 'NAR'),
  (783, 'El Charco', 'NAR'),
  (784, 'El Peñol', 'NAR'),
  (785, 'El Rosario', 'NAR'),
  (786, 'El Tablón de Gómez', 'NAR'),
  (787, 'El Tambo', 'NAR'),
  (788, 'Francisco Pizarro', 'NAR'),
  (789, 'Funes', 'NAR'),
  (790, 'Guachucal', 'NAR'),
  (791, 'Guaitarilla', 'NAR'),
  (792, 'Gualmatán', 'NAR'),
  (793, 'Iles', 'NAR'),
  (794, 'Imués', 'NAR'),
  (795, 'Ipiales', 'NAR'),
  (796, 'La Cruz', 'NAR'),
  (797, 'La Florida', 'NAR'),
  (798, 'La Llanada', 'NAR'),
  (799, 'La Tola', 'NAR'),
  (800, 'La Unión', 'NAR'),
  (801, 'Leiva', 'NAR'),
  (802, 'Linares', 'NAR'),
  (803, 'Los Andes', 'NAR'),
  (804, 'Magüí Payán', 'NAR'),
  (805, 'Mallama', 'NAR'),
  (806, 'Mosquera', 'NAR'),
  (807, 'Nariño', 'NAR'),
  (808, 'Olaya Herrera', 'NAR'),
  (809, 'Ospina', 'NAR'),
  (810, 'Pasto', 'NAR'),
  (811, 'Policarpa', 'NAR'),
  (812, 'Potosí', 'NAR'),
  (813, 'Providencia', 'NAR'),
  (814, 'Puerres', 'NAR'),
  (815, 'Pupiales', 'NAR'),
  (816, 'Ricaurte', 'NAR'),
  (817, 'Roberto Payán', 'NAR'),
  (818, 'Samaniego', 'NAR'),
  (819, 'San Andres de Tumaco', 'NAR'),
  (820, 'San Bernardo', 'NAR'),
  (821, 'San Lorenzo', 'NAR'),
  (822, 'San Pablo', 'NAR'),
  (823, 'San Pedro de Cartago', 'NAR'),
  (824, 'Sandoná', 'NAR'),
  (825, 'Santa Bárbara', 'NAR'),
  (826, 'Santacruz', 'NAR'),
  (827, 'Sapuyes', 'NAR'),
  (828, 'Taminango', 'NAR'),
  (829, 'Tangua', 'NAR'),
  (830, 'Túquerres', 'NAR'),
  (831, 'Yacuanquer', 'NAR'),
  (832, 'Arboledas', 'NSA'),
  (833, 'Bochalema', 'NSA'),
  (834, 'Bucarasica', 'NSA'),
  (835, 'Chinácota', 'NSA'),
  (836, 'Chitagá', 'NSA'),
  (837, 'Convención', 'NSA'),
  (838, 'Cucutilla', 'NSA'),
  (839, 'Cáchira', 'NSA'),
  (840, 'Cácota', 'NSA'),
  (841, 'Cúcuta', 'NSA'),
  (842, 'Duranía', 'NSA'),
  (843, 'El Carmen', 'NSA'),
  (844, 'El Tarra', 'NSA'),
  (845, 'El Zulia', 'NSA'),
  (846, 'Gramalote', 'NSA'),
  (847, 'Hacarí', 'NSA'),
  (848, 'Herrán', 'NSA'),
  (849, 'La Esperanza', 'NSA'),
  (850, 'La Playa de Belén', 'NSA'),
  (851, 'Labateca', 'NSA'),
  (852, 'Los Patios', 'NSA'),
  (853, 'Lourdes', 'NSA'),
  (854, 'Mutiscua', 'NSA'),
  (855, 'Ocaña', 'NSA'),
  (856, 'Pamplona', 'NSA'),
  (857, 'Pamplonita', 'NSA'),
  (858, 'Puerto Santander', 'NSA'),
  (859, 'Ragonvalia', 'NSA'),
  (860, 'Salazar de Las Palmas', 'NSA'),
  (861, 'San Calixto', 'NSA'),
  (862, 'San Cayetano', 'NSA'),
  (863, 'Santiago', 'NSA'),
  (864, 'Sardinata', 'NSA'),
  (865, 'Silos', 'NSA'),
  (866, 'Teorama', 'NSA'),
  (867, 'Tibú', 'NSA'),
  (868, 'Toledo', 'NSA'),
  (869, 'Villa Caro', 'NSA'),
  (870, 'Villa del Rosario', 'NSA'),
  (871, 'Ábrego', 'NSA'),
  (872, 'Colón', 'PUT'),
  (873, 'Mocoa', 'PUT'),
  (874, 'Orito', 'PUT'),
  (875, 'Puerto Asís', 'PUT'),
  (876, 'Puerto Caicedo', 'PUT'),
  (877, 'Puerto Guzmán', 'PUT'),
  (878, 'Puerto Leguízamo', 'PUT'),
  (879, 'San Francisco', 'PUT'),
  (880, 'San Miguel', 'PUT'),
  (881, 'Santiago', 'PUT'),
  (882, 'Sibundoy', 'PUT'),
  (883, 'Valle del Guamuez', 'PUT'),
  (884, 'Villagarzón', 'PUT'),
  (885, 'Armenia', 'QUI'),
  (886, 'Buenavista', 'QUI'),
  (887, 'Calarcá', 'QUI'),
  (888, 'Circasia', 'QUI'),
  (889, 'Córdoba', 'QUI'),
  (890, 'Filandia', 'QUI'),
  (891, 'Génova', 'QUI'),
  (892, 'La Tebaida', 'QUI'),
  (893, 'Montenegro', 'QUI'),
  (894, 'Pijao', 'QUI'),
  (895, 'Quimbaya', 'QUI'),
  (896, 'Salento', 'QUI'),
  (897, 'Apía', 'RIS'),
  (898, 'Balboa', 'RIS'),
  (899, 'Belén de Umbría', 'RIS'),
  (900, 'Dosquebradas', 'RIS'),
  (901, 'Guática', 'RIS'),
  (902, 'La Celia', 'RIS'),
  (903, 'La Virginia', 'RIS'),
  (904, 'Marsella', 'RIS'),
  (905, 'Mistrató', 'RIS'),
  (906, 'Pereira', 'RIS'),
  (907, 'Pueblo Rico', 'RIS'),
  (908, 'Quinchía', 'RIS'),
  (909, 'Santa Rosa de Cabal', 'RIS'),
  (910, 'Santuario', 'RIS'),
  (911, 'Aguada', 'SAN'),
  (912, 'Albania', 'SAN'),
  (913, 'Aratoca', 'SAN'),
  (914, 'Barbosa', 'SAN'),
  (915, 'Barichara', 'SAN'),
  (916, 'Barrancabermeja', 'SAN'),
  (917, 'Betulia', 'SAN'),
  (918, 'Bolívar', 'SAN'),
  (919, 'Bucaramanga', 'SAN'),
  (920, 'Cabrera', 'SAN'),
  (921, 'California', 'SAN'),
  (922, 'Capitanejo', 'SAN'),
  (923, 'Carcasí', 'SAN'),
  (924, 'Cepitá', 'SAN'),
  (925, 'Cerrito', 'SAN'),
  (926, 'Charalá', 'SAN'),
  (927, 'Charta', 'SAN'),
  (928, 'Chima', 'SAN'),
  (929, 'Chipatá', 'SAN'),
  (930, 'Cimitarra', 'SAN'),
  (931, 'Concepción', 'SAN'),
  (932, 'Confines', 'SAN'),
  (933, 'Contratación', 'SAN'),
  (934, 'Coromoro', 'SAN'),
  (935, 'Curití', 'SAN'),
  (936, 'El Carmen de Chucurí', 'SAN'),
  (937, 'El Guacamayo', 'SAN'),
  (938, 'El Peñón', 'SAN'),
  (939, 'El Playón', 'SAN'),
  (940, 'Encino', 'SAN'),
  (941, 'Enciso', 'SAN'),
  (942, 'Floridablanca', 'SAN'),
  (943, 'Florián', 'SAN'),
  (944, 'Galán', 'SAN'),
  (945, 'Guaca', 'SAN'),
  (946, 'Guadalupe', 'SAN'),
  (947, 'Guapotá', 'SAN'),
  (948, 'Guavatá', 'SAN'),
  (949, 'Gámbita', 'SAN'),
  (950, 'Güepsa', 'SAN'),
  (951, 'Hato', 'SAN'),
  (952, 'Jesús María', 'SAN'),
  (953, 'Jordán', 'SAN'),
  (954, 'La Belleza', 'SAN'),
  (955, 'La Paz', 'SAN'),
  (956, 'Landázuri', 'SAN'),
  (957, 'Lebrija', 'SAN'),
  (958, 'Los Santos', 'SAN'),
  (959, 'Macaravita', 'SAN'),
  (960, 'Matanza', 'SAN'),
  (961, 'Mogotes', 'SAN'),
  (962, 'Molagavita', 'SAN'),
  (963, 'Málaga', 'SAN'),
  (964, 'Ocamonte', 'SAN'),
  (965, 'Oiba', 'SAN'),
  (966, 'Onzaga', 'SAN'),
  (967, 'Palmar', 'SAN'),
  (968, 'Palmas del Socorro', 'SAN'),
  (969, 'Piedecuesta', 'SAN'),
  (970, 'Pinchote', 'SAN'),
  (971, 'Puente Nacional', 'SAN'),
  (972, 'Puerto Parra', 'SAN'),
  (973, 'Puerto Wilches', 'SAN'),
  (974, 'Páramo', 'SAN'),
  (975, 'Rionegro', 'SAN'),
  (976, 'Sabana de Torres', 'SAN'),
  (977, 'San Andrés', 'SAN'),
  (978, 'San Benito', 'SAN'),
  (979, 'San Gil', 'SAN'),
  (980, 'San Joaquín', 'SAN'),
  (981, 'San José de Miranda', 'SAN'),
  (982, 'San Juan de Girón', 'SAN'),
  (983, 'San Miguel', 'SAN'),
  (984, 'San Vicente de Chucurí', 'SAN'),
  (985, 'Santa Bárbara', 'SAN'),
  (986, 'Santa Helena del Opón', 'SAN'),
  (987, 'Simacota', 'SAN'),
  (988, 'Socorro', 'SAN'),
  (989, 'Suaita', 'SAN'),
  (990, 'Sucre', 'SAN'),
  (991, 'Suratá', 'SAN'),
  (992, 'Tona', 'SAN'),
  (993, 'Valle de San José', 'SAN'),
  (994, 'Vetas', 'SAN'),
  (995, 'Villanueva', 'SAN'),
  (996, 'Vélez', 'SAN'),
  (997, 'Zapatoca', 'SAN'),
  (998, 'Buenavista', 'SUC'),
  (999, 'Caimito', 'SUC'),
  (1000, 'Chalán', 'SUC'),
  (1001, 'Colosó', 'SUC'),
  (1002, 'Corozal', 'SUC'),
  (1003, 'Coveñas', 'SUC'),
  (1004, 'El Roble', 'SUC'),
  (1005, 'Galeras', 'SUC'),
  (1006, 'Guaranda', 'SUC'),
  (1007, 'La Unión', 'SUC'),
  (1008, 'Los Palmitos', 'SUC'),
  (1009, 'Majagual', 'SUC'),
  (1010, 'Morroa', 'SUC'),
  (1011, 'Ovejas', 'SUC'),
  (1012, 'Palmito', 'SUC'),
  (1013, 'Sampués', 'SUC'),
  (1014, 'San Benito Abad', 'SUC'),
  (1015, 'San Juan de Betulia', 'SUC'),
  (1016, 'San Luis de Sincé', 'SUC'),
  (1017, 'San Marcos', 'SUC'),
  (1018, 'San Onofre', 'SUC'),
  (1019, 'San Pedro', 'SUC'),
  (1020, 'Santiago de Tolú', 'SUC'),
  (1021, 'Sincelejo', 'SUC'),
  (1022, 'Sucre', 'SUC'),
  (1023, 'Tolú Viejo', 'SUC'),
  (1024, 'Alpujarra', 'TOL'),
  (1025, 'Alvarado', 'TOL'),
  (1026, 'Ambalema', 'TOL'),
  (1027, 'Anzoátegui', 'TOL'),
  (1028, 'Armero', 'TOL'),
  (1029, 'Ataco', 'TOL'),
  (1030, 'Cajamarca', 'TOL'),
  (1031, 'Carmen de Apicalá', 'TOL'),
  (1032, 'Casabianca', 'TOL'),
  (1033, 'Chaparral', 'TOL'),
  (1034, 'Coello', 'TOL'),
  (1035, 'Coyaima', 'TOL'),
  (1036, 'Cunday', 'TOL'),
  (1037, 'Dolores', 'TOL'),
  (1038, 'Espinal', 'TOL'),
  (1039, 'Falán', 'TOL'),
  (1040, 'Flandes', 'TOL'),
  (1041, 'Fresno', 'TOL'),
  (1042, 'Guamo', 'TOL'),
  (1043, 'Herveo', 'TOL'),
  (1044, 'Honda', 'TOL'),
  (1045, 'Ibagué', 'TOL'),
  (1046, 'Icononzo', 'TOL'),
  (1047, 'Lérida', 'TOL'),
  (1048, 'Líbano', 'TOL'),
  (1049, 'Melgar', 'TOL'),
  (1050, 'Murillo', 'TOL'),
  (1051, 'Natagaima', 'TOL'),
  (1052, 'Ortega', 'TOL'),
  (1053, 'Palocabildo', 'TOL'),
  (1054, 'Piedras', 'TOL'),
  (1055, 'Planadas', 'TOL'),
  (1056, 'Prado', 'TOL'),
  (1057, 'Purificación', 'TOL'),
  (1058, 'Rioblanco', 'TOL'),
  (1059, 'Roncesvalles', 'TOL'),
  (1060, 'Rovira', 'TOL'),
  (1061, 'Saldaña', 'TOL'),
  (1062, 'San Antonio', 'TOL'),
  (1063, 'San Luis', 'TOL'),
  (1064, 'San Sebastián de Mariquita', 'TOL'),
  (1065, 'Santa Isabel', 'TOL'),
  (1066, 'Suárez', 'TOL'),
  (1067, 'Valle de San Juan', 'TOL'),
  (1068, 'Venadillo', 'TOL'),
  (1069, 'Villahermosa', 'TOL'),
  (1070, 'Villarrica', 'TOL'),
  (1071, 'Alcalá', 'VAC'),
  (1072, 'Andalucía', 'VAC'),
  (1073, 'Ansermanuevo', 'VAC'),
  (1074, 'Argelia', 'VAC'),
  (1075, 'Bolívar', 'VAC'),
  (1076, 'Buenaventura', 'VAC'),
  (1077, 'Bugalagrande', 'VAC'),
  (1078, 'Caicedonia', 'VAC'),
  (1079, 'Cali', 'VAC'),
  (1080, 'Calima', 'VAC'),
  (1081, 'Candelaria', 'VAC'),
  (1082, 'Cartago', 'VAC'),
  (1083, 'Dagua', 'VAC'),
  (1084, 'El Cairo', 'VAC'),
  (1085, 'El Cerrito', 'VAC'),
  (1086, 'El Dovio', 'VAC'),
  (1087, 'El Águila', 'VAC'),
  (1088, 'Florida', 'VAC'),
  (1089, 'Ginebra', 'VAC'),
  (1090, 'Guacarí', 'VAC'),
  (1091, 'Guadalajara de Buga', 'VAC'),
  (1092, 'Jamundí', 'VAC'),
  (1093, 'La Cumbre', 'VAC'),
  (1094, 'La Unión', 'VAC'),
  (1095, 'La Victoria', 'VAC'),
  (1096, 'Obando', 'VAC'),
  (1097, 'Palmira', 'VAC'),
  (1098, 'Pradera', 'VAC'),
  (1099, 'Restrepo', 'VAC'),
  (1100, 'Riofrío', 'VAC'),
  (1101, 'Roldanillo', 'VAC'),
  (1102, 'San Pedro', 'VAC'),
  (1103, 'Sevilla', 'VAC'),
  (1104, 'Toro', 'VAC'),
  (1105, 'Trujillo', 'VAC'),
  (1106, 'Tuluá', 'VAC'),
  (1107, 'Ulloa', 'VAC'),
  (1108, 'Versalles', 'VAC'),
  (1109, 'Vijes', 'VAC'),
  (1110, 'Yotoco', 'VAC'),
  (1111, 'Yumbo', 'VAC'),
  (1112, 'Zarzal', 'VAC'),
  (1113, 'Carurú', 'VAU'),
  (1114, 'Mitú', 'VAU'),
  (1115, 'Pacoa', 'VAU'),
  (1116, 'Papunaua', 'VAU'),
  (1117, 'Taraira', 'VAU'),
  (1118, 'Yavaraté', 'VAU'),
  (1119, 'Cumaribo', 'VID'),
  (1120, 'La Primavera', 'VID'),
  (1121, 'Puerto Carreño', 'VID'),
  (1122, 'Santa Rosalía', 'VID'),
)
