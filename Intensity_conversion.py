import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# Constants
# --------------------------------------------------
H = 6.62607015e-34
C = 299792458
NA = 6.02214076e23
K_M = 683.0

st.set_page_config(
    page_title="Optical Unit Converter",
    page_icon="💡",
    layout="centered",
)

UNITS = [
    "μmol m⁻² s⁻¹",
    "W",
    "mW",
    "lm",
    "mcd",
]

# Approximate CIE 1931 photopic luminous efficiency V(lambda).
CIE_VALUES = {
    380: 0.000039, 390: 0.000120, 400: 0.000396,
    410: 0.001210, 420: 0.004000, 430: 0.011600,
    440: 0.023000, 450: 0.038000, 460: 0.060000,
    470: 0.091000, 480: 0.139020, 490: 0.208020,
    500: 0.323000, 510: 0.503000, 520: 0.710000,
    530: 0.862000, 540: 0.954000, 550: 0.995000,
    560: 0.995000, 570: 0.952000, 580: 0.870000,
    590: 0.757000, 600: 0.631000, 610: 0.503000,
    620: 0.381000, 630: 0.265000, 640: 0.175000,
    650: 0.107000, 660: 0.061000, 670: 0.032000,
    680: 0.017000, 690: 0.008210, 700: 0.004102,
    710: 0.002091, 720: 0.001047, 730: 0.000520,
    740: 0.000249, 750: 0.000120, 760: 0.000060,
    770: 0.000030, 780: 0.000015,
}


def photopic_efficiency(wavelength_nm):
    """Interpolate the approximate CIE V(lambda) table."""

    wavelengths = np.array(list(CIE_VALUES.keys()), dtype=float)
    efficiencies = np.array(list(CIE_VALUES.values()), dtype=float)

    if not 380 <= wavelength_nm <= 780:
        raise ValueError("Supported wavelengths are 380–780 nm.")

    return float(np.interp(
        wavelength_nm, wavelengths, efficiencies
    ))


def calculate_conversions(
    value,
    input_unit,
    output_units,
    wavelength_nm=None,
    radius_m=None,
    theta_half_deg=None,
):
    """
    Convert between photon flux density, W, mW, lm and mcd.

    Assumes uniform luminous intensity within a circular emission cone.
    """

    if value < 0:
        raise ValueError("Input value must be non-negative.")

    # Determine whether wavelength is required.
    photometric_units = ("lm", "mcd")
    photon_unit = "μmol m⁻² s⁻¹"

    needs_wavelength = (
        input_unit == photon_unit
        or input_unit in photometric_units
        or any(
            u == photon_unit or u in photometric_units
            for u in output_units
        )
    )

    if needs_wavelength and wavelength_nm is None:
        raise ValueError("Wavelength is required.")

    if wavelength_nm is not None and not 380 <= wavelength_nm <= 780:
        raise ValueError("Supported wavelengths are 380–780 nm.")

    # Radius is only required for photon flux density.
    needs_area = (
        input_unit == photon_unit
        or photon_unit in output_units
    )

    if needs_area and (radius_m is None or radius_m <= 0):
        raise ValueError("Radius must be greater than zero.")

    # Half viewing angle is required for lm/mcd conversions.
    needs_angle = (
        input_unit == "mcd"
        or "mcd" in output_units
        or input_unit == "lm"
        or "lm" in output_units
    )

    if needs_angle and theta_half_deg is None:
        raise ValueError("Half viewing angle is required.")

    if needs_angle and not 0 < theta_half_deg <= 180:
        raise ValueError(
            "Half viewing angle must be greater than 0 and at most 180 degrees."
        )

    # Calculate illuminated area.
    if needs_area:
        area_m2 = np.pi * radius_m**2
    else:
        area_m2 = None

    # Calculate emission solid angle from half viewing angle.
    if needs_angle:
        theta_rad = np.radians(theta_half_deg)

        solid_angle_sr = (
            2 * np.pi * (1 - np.cos(theta_rad))
        )
    else:
        solid_angle_sr = None

    # Photopic luminous efficiency.
    if needs_wavelength:
        v_lambda = photopic_efficiency(wavelength_nm)
    else:
        v_lambda = None

    # --------------------------------------------------
    # Convert input to radiant power (W).
    # --------------------------------------------------

    if input_unit == "W":
        power_w = value

    elif input_unit == "mW":
        power_w = value / 1000.0

    elif input_unit == "lm":
        power_w = value / (K_M * v_lambda)

    elif input_unit == "mcd":
        intensity_cd = value / 1000.0

        luminous_flux_lm = (
            intensity_cd * solid_angle_sr
        )

        power_w = luminous_flux_lm / (K_M * v_lambda)

    elif input_unit == photon_unit:
        energy_per_photon = (
            H * C / (wavelength_nm * 1e-9)
        )

        photon_rate_mol_s = value * area_m2

        power_w = (
            photon_rate_mol_s * 1e-6
            * NA * energy_per_photon
        )

    else:
        raise ValueError("Unsupported input unit.")

    # --------------------------------------------------
    # Convert radiant power (W) to requested units.
    # --------------------------------------------------

    results = {}

    if needs_wavelength:
        energy_per_photon = (
            H * C / (wavelength_nm * 1e-9)
        )

    for unit in output_units:

        if unit == "W":
            results[unit] = power_w

        elif unit == "mW":
            results[unit] = power_w * 1000.0

        elif unit == "lm":
            results[unit] = (
                K_M * v_lambda * power_w
            )

        elif unit == "mcd":
            luminous_flux_lm = (
                K_M * v_lambda * power_w
            )

            intensity_cd = (
                luminous_flux_lm / solid_angle_sr
            )

            results[unit] = intensity_cd * 1000.0

        elif unit == photon_unit:
            photon_rate_mol_s = (
                power_w / energy_per_photon / NA
            )

            results[unit] = (
                photon_rate_mol_s * 1e6 / area_m2
            )

    return results


# --------------------------------------------------
# User interface
# --------------------------------------------------

st.title("💡 Optical Unit Converter")

st.write(
    "Convert photon flux density (PAR), radiant power, "
    "luminous flux and luminous intensity for monochromatic light."
)

st.info(
    "Select one input unit and one or more output units."
)

# Input and output unit selectors.
input_unit = st.selectbox(
    "Convert from",
    UNITS,
    key="input_unit",
)

output_units = st.multiselect(
    "Convert to",
    [u for u in UNITS if u != input_unit],
    default=[u for u in UNITS if u != input_unit],
    key="output_units",
)

# Determine which additional inputs are required.
needs_photon = (
    input_unit == "μmol m⁻² s⁻¹"
    or "μmol m⁻² s⁻¹" in output_units
)

needs_photometric = (
    input_unit in ("lm", "mcd")
    or any(u in ("lm", "mcd") for u in output_units)
)

needs_wavelength = needs_photon or needs_photometric

needs_angle = (
    input_unit in ("lm", "mcd")
    or any(u in ("lm", "mcd") for u in output_units)
)

# Input value.
value = st.number_input(
    f"Input value ({input_unit})",
    min_value=0.0,
    value=1.0,
    format="%.8g",
    key="input_value",
)

# Wavelength.
if needs_wavelength:
    wavelength_nm = st.number_input(
        "Wavelength (nm)",
        min_value=380.0,
        max_value=780.0,
        value=555.0,
        step=1.0,
        help="The photopic model supports 380–780 nm.",
        key="wavelength_nm",
    )
else:
    wavelength_nm = None

# Radius.
if needs_photon:
    radius_m = st.number_input(
        "Radius of illuminated area (m)",
        min_value=0.000001,
        value=1.0,
        format="%.8g",
        help="Required for photon flux density conversions.",
        key="radius_m",
    )
else:
    radius_m = None

# Half viewing angle.
if needs_angle:
    theta_half_deg = st.number_input(
        "Half viewing angle θ₁/₂ (degrees)",
        min_value=0.001,
        max_value=180.0,
        value=30.0,
        step=1.0,
        help=(
            "Angle measured from the optical axis to the edge "
            "of the emission cone."
        ),
        key="theta_half_deg",
    )
else:
    theta_half_deg = None

# --------------------------------------------------
# Conversion results
# --------------------------------------------------

if not output_units:

    st.info("Select at least one output unit.")

else:

    try:

        results = calculate_conversions(
            value=value,
            input_unit=input_unit,
            output_units=output_units,
            wavelength_nm=wavelength_nm,
            radius_m=radius_m,
            theta_half_deg=theta_half_deg,
        )

        st.subheader("Conversion results")

        df = pd.DataFrame({
            "Output unit": list(results.keys()),
            "Converted value": [
                f"{result:.8g}"
                for result in results.values()
            ],
        })

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
        )

        # Display calculation parameters.
        if needs_wavelength:
            caption = (
                f"Wavelength: {wavelength_nm:g} nm"
                f" | V(λ): {photopic_efficiency(wavelength_nm):.6g}"
            )

            st.caption(caption)

        if needs_angle:
            omega = (
                2 * np.pi *
                (1 - np.cos(np.radians(theta_half_deg)))
            )

            st.caption(
                f"Half viewing angle: {theta_half_deg:g}°"
                f" | Solid angle: {omega:.6g} sr"
            )

    except ValueError as error:
        st.error(str(error))


# --------------------------------------------------
# Notes
# --------------------------------------------------

st.divider()

st.caption(
    "Note: Photometric conversions depend on wavelength and "
    "the CIE 1931 photopic response. Luminous intensity and "
    "luminous flux conversions assume uniform intensity "
    "within a circular emission cone. Photon flux density "
    "is expressed in µmol m⁻² s⁻¹."
)
